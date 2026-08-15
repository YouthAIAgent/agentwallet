"""Solana RPC operations -- ported from moltfarm lib/wallet.py and lib/signer.py.

Provides: balance queries, SOL/SPL transfers, transaction signing,
confirmation polling, and decode utilities.
"""

import base64 as b64

import base58
import httpx
from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.presigner import Presigner
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction, VersionedTransaction

from .config import get_settings
from .exceptions import InsufficientBalanceError, RetryableError, TransactionFailedError
from .logging import get_logger
from .retry import retry

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rpc_url() -> str:
    return get_settings().solana_rpc_url


def _rpc_timeout() -> int:
    return get_settings().rpc_timeout


async def _rpc_post(
    client: httpx.AsyncClient,
    method: str,
    params: list,
    rpc_id: int = 1,
) -> httpx.Response:
    """POST a JSON-RPC call with retry-on-429/5xx backoff.

    The public devnet RPC rate-limits aggressively (429) and is load-balanced
    with eventual consistency, so transient failures are retried with
    exponential backoff + jitter instead of failing the whole request.
    """
    import asyncio
    import random

    max_attempts = 4
    for attempt in range(max_attempts):
        resp = await client.post(
            _rpc_url(),
            json={
                "jsonrpc": "2.0",
                "id": rpc_id + attempt,
                "method": method,
                "params": params,
            },
            timeout=_rpc_timeout(),
        )
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_attempts - 1:
            delay = min(1.0 * (2**attempt), 8.0) + random.uniform(0, 0.5)
            logger.warning(
                "rpc_retry",
                method=method,
                status=resp.status_code,
                attempt=attempt + 1,
                backoff_s=round(delay, 1),
            )
            await asyncio.sleep(delay)
            continue
        resp.raise_for_status()
        return resp
    raise RetryableError(f"RPC {method} failed after {max_attempts} attempts")


def load_platform_keypair() -> Keypair:
    """Load the platform wallet keypair (escrow custody / fee signer).

    Prefers PLATFORM_PRIVATE_KEY_HEX (hex-encoded 64-byte secret key); falls
    back to the gitignored packages/api/.platform-keypair.json file.

    Raises ValueError if no key is configured.
    """
    import json as _json
    from pathlib import Path

    hex_key = get_settings().platform_private_key_hex
    if not hex_key:
        keyfile = Path("packages/api/.platform-keypair.json")
        if keyfile.exists():
            try:
                hex_key = _json.loads(keyfile.read_text()).get("secret_key_hex", "")
            except Exception:
                hex_key = ""
    if not hex_key:
        raise ValueError(
            "Platform private key not configured: set PLATFORM_PRIVATE_KEY_HEX or "
            "place packages/api/.platform-keypair.json"
        )
    return Keypair.from_bytes(bytes.fromhex(hex_key))


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


@retry()
async def get_balance(client: httpx.AsyncClient, address: str) -> int:
    """Get SOL balance in lamports. Raises RetryableError on RPC failure."""
    resp = await _rpc_post(client, "getBalance", [address])
    body = resp.json()
    if "error" in body:
        raise RetryableError(f"RPC error: {body['error']}")
    result = body.get("result")
    if result is None:
        raise RetryableError("RPC returned no result")
    return result.get("value", 0)


async def get_balance_sol(client: httpx.AsyncClient, address: str) -> float | None:
    """Get SOL balance as float, or None on failure."""
    try:
        return (await get_balance(client, address)) / 1e9
    except Exception as e:
        logger.error("balance_check_failed", address=address[:16], error=str(e))
        return None


# ---------------------------------------------------------------------------
# Transfer SOL (ported from moltfarm lib/wallet.py transfer_sol)
# ---------------------------------------------------------------------------


@retry()
async def transfer_sol(
    client: httpx.AsyncClient,
    from_keypair: Keypair,
    to_address: str,
    lamports: int,
    fee_lamports: int = 0,
    fee_recipient: str | None = None,
) -> str:
    """Transfer SOL with optional platform fee.

    If fee_lamports > 0 and fee_recipient is set, an additional transfer
    instruction is added atomically in the same transaction.

    Returns the transaction signature.
    """
    from_addr = str(from_keypair.pubkey())

    # Validate balance
    bal = await get_balance(client, from_addr)
    tx_fee = 5000  # base tx fee
    total_needed = lamports + fee_lamports + tx_fee
    if bal < total_needed:
        raise InsufficientBalanceError(available=bal, required=total_needed)

    # Get blockhash
    resp = await _rpc_post(client, "getLatestBlockhash", [])
    bh_data = resp.json()
    if "error" in bh_data:
        raise RetryableError(f"Blockhash RPC error: {bh_data['error']}")
    bh = Hash.from_string(bh_data["result"]["value"]["blockhash"])

    # Build instructions
    instructions = [
        transfer(
            TransferParams(
                from_pubkey=from_keypair.pubkey(),
                to_pubkey=Pubkey.from_string(to_address),
                lamports=lamports,
            )
        )
    ]

    if fee_lamports > 0 and fee_recipient:
        instructions.append(
            transfer(
                TransferParams(
                    from_pubkey=from_keypair.pubkey(),
                    to_pubkey=Pubkey.from_string(fee_recipient),
                    lamports=fee_lamports,
                )
            )
        )

    msg = Message(instructions, from_keypair.pubkey())
    tx = Transaction([from_keypair], msg, bh)
    tx_b58 = base58.b58encode(bytes(tx)).decode()

    # Send
    resp = await _rpc_post(client, "sendTransaction", [tx_b58, {"encoding": "base58"}], rpc_id=2)
    result = resp.json()

    if result.get("error"):
        raise RetryableError(f"sendTransaction error: {result['error']}")

    sig = result.get("result")
    if not sig:
        raise RetryableError(f"sendTransaction returned no signature: {result}")

    logger.info(
        "sol_transferred",
        from_addr=from_addr[:16],
        to_addr=to_address[:16],
        lamports=lamports,
        fee_lamports=fee_lamports,
        signature=sig[:24],
    )
    return sig


# ---------------------------------------------------------------------------
# Confirm Transaction (ported from moltfarm lib/wallet.py confirm_transaction)
# ---------------------------------------------------------------------------


async def confirm_transaction(
    client: httpx.AsyncClient,
    signature: str,
    max_polls: int | None = None,
    poll_interval: float | None = None,
) -> bool:
    """Poll getSignatureStatuses until confirmed/finalized or timeout.

    Returns True if confirmed, False if timed out or errored.
    """
    import asyncio

    settings = get_settings()
    max_polls = max_polls or settings.rpc_confirm_max_polls
    poll_interval = poll_interval or settings.rpc_confirm_poll_interval

    for _i in range(max_polls):
        try:
            resp = await _rpc_post(
                client,
                "getSignatureStatuses",
                [[signature], {"searchTransactionHistory": True}],
            )
            body = resp.json()
            statuses = body.get("result", {}).get("value", [])
            if statuses and statuses[0]:
                status = statuses[0]
                if status.get("err"):
                    logger.error("tx_failed_onchain", signature=signature[:24], err=status["err"])
                    return False
                conf = status.get("confirmationStatus", "")
                if conf in ("confirmed", "finalized"):
                    logger.info("tx_confirmed", signature=signature[:24], status=conf)
                    return True
        except Exception as e:
            logger.warning("confirmation_poll_error", error=str(e))
        await asyncio.sleep(poll_interval)

    logger.warning("tx_confirmation_timeout", signature=signature[:24])
    return False


async def get_parsed_transaction(
    client: httpx.AsyncClient,
    signature: str,
) -> dict | None:
    """Fetch a parsed transaction from the RPC.

    Returns the parsed transaction body (the `result` object) or None if
    the transaction is not found / not yet available.

    Some RPC endpoints return null for `getParsedTransaction` (notably
    local test-validators), but work fine with `getTransaction` using the
    `jsonParsed` encoding -- so we fall back to that.
    """
    for method in ("getParsedTransaction", "getTransaction"):
        try:
            resp = await _rpc_post(
                client,
                method,
                [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0,
                        "commitment": "confirmed",
                    },
                ],
            )
            body = resp.json()
            if body.get("error"):
                logger.warning("parsed_tx_rpc_error", signature=signature[:24], error=body["error"])
                continue
            result = body.get("result")
            if isinstance(result, dict):
                return result
        except Exception as e:
            logger.warning("parsed_tx_fetch_error", signature=signature[:24], error=str(e))
    return None


async def verify_transfer_on_chain(
    client: httpx.AsyncClient,
    signature: str,
    expected_pay_to: str,
    expected_amount: int,
    token_mint: str | None = None,
) -> dict:
    """Verify that a confirmed transaction paid `expected_pay_to` at least `expected_amount`.

    Uses getParsedTransaction to extract the real payer, recipient, and amount
    from the on-chain record -- never trusts client-supplied payload fields.

    Supports native SOL transfers (lamports) and SPL token transfers (USDC etc).

    Returns dict with:
        valid, payer, payee, amount, token_mint, error
    """
    # Poll for the parsed tx -- right after submission the RPC may not have
    # full parsed data yet, and some validators return partial results.
    import asyncio

    tx = None
    for _attempt in range(6):
        tx = await get_parsed_transaction(client, signature)
        if tx and tx.get("meta") and (tx.get("meta") or {}).get("preBalances"):
            break
        await asyncio.sleep(0.5)
    if not tx:
        return {"valid": False, "error": "Transaction not found on-chain"}

    meta = tx.get("meta") or {}
    if meta.get("err"):
        return {"valid": False, "error": f"Transaction failed on-chain: {meta.get('err')}"}

    tx_obj = tx.get("transaction") or {}
    message = tx_obj.get("message") or {}
    account_keys = message.get("accountKeys", [])

    logger.debug(
        "x402_parsed_tx",
        signature=signature[:24],
        keys_type=type(account_keys).__name__,
        keys_len=len(account_keys),
    )

    if not account_keys:
        return {"valid": False, "error": "Transaction has no account keys"}

    # Payer is the fee payer (first signer / first account with signer=true)
    payer = None
    for acc in account_keys:
        if isinstance(acc, dict) and acc.get("signer"):
            payer = acc.get("pubkey")
            break
    if not payer and isinstance(account_keys[0], str):
        payer = account_keys[0]
    if not payer:
        payer = str(account_keys[0]) if isinstance(account_keys[0], dict) else account_keys[0]
    logger.debug("x402_parsed_tx_payer", signature=signature[:24], payer=payer, keys_sample=str(account_keys[:2])[:300])

    resolved_keys: list[str] = []
    for acc in account_keys:
        if isinstance(acc, dict):
            resolved_keys.append(acc.get("pubkey", ""))
        elif isinstance(acc, str):
            resolved_keys.append(acc)
        else:
            resolved_keys.append("")

    # Normalize expected pay-to
    expected_pay_to = expected_pay_to.strip()

    if token_mint:
        # SPL token transfer -- inspect pre/post token balances for payee ATA
        payee_idx = None
        if expected_pay_to in resolved_keys:
            payee_idx = resolved_keys.index(expected_pay_to)
        else:
            # payee may be the associated token account owner -- find owner match
            pre_tokens = meta.get("preTokenBalances") or []
            for entry in pre_tokens:
                if entry.get("owner") == expected_pay_to:
                    payee_idx = entry.get("accountIndex")
                    break

        if payee_idx is None:
            return {"valid": False, "error": "Payee not found in transaction accounts"}

        received = 0
        paid = 0
        pre_tokens = meta.get("preTokenBalances") or []
        post_tokens = meta.get("postTokenBalances") or []
        pre_map = {e.get("accountIndex"): e for e in pre_tokens}
        post_map = {e.get("accountIndex"): e for e in post_tokens}
        indices = set(pre_map) | set(post_map)
        for idx in indices:
            pre = pre_map.get(idx, {}).get("uiTokenAmount") or {}
            post = post_map.get(idx, {}).get("uiTokenAmount") or {}
            mint = post_map.get(idx, {}).get("mint") or pre_map.get(idx, {}).get("mint") or ""
            owner = post_map.get(idx, {}).get("owner") or pre_map.get(idx, {}).get("owner") or ""
            if mint != token_mint:
                continue
            pre_amt = int(pre.get("amount", 0) or 0)
            post_amt = int(post.get("amount", 0) or 0)
            if owner == expected_pay_to and post_amt > pre_amt:
                received += post_amt - pre_amt
            if owner == payer and pre_amt > post_amt:
                paid += pre_amt - post_amt

        if received < expected_amount:
            return {
                "valid": False,
                "payer": payer,
                "payee": expected_pay_to,
                "amount": received,
                "token_mint": token_mint,
                "error": f"Payee received {received}, expected at least {expected_amount}",
            }

        return {
            "valid": True,
            "payer": payer,
            "payee": expected_pay_to,
            "amount": received,
            "token_mint": token_mint,
            "error": None,
        }

    # Native SOL transfer -- inspect pre/post SOL balances
    payee_idx = None
    if expected_pay_to in resolved_keys:
        payee_idx = resolved_keys.index(expected_pay_to)
    if payee_idx is None:
        return {"valid": False, "error": "Payee not found in transaction accounts"}

    pre_balances = meta.get("preBalances", []) or []
    post_balances = meta.get("postBalances", []) or []
    if payee_idx >= len(pre_balances) or payee_idx >= len(post_balances):
        return {"valid": False, "error": "Balance data unavailable for payee"}

    received = post_balances[payee_idx] - pre_balances[payee_idx]
    if received < expected_amount:
        return {
            "valid": False,
            "payer": payer,
            "payee": expected_pay_to,
            "amount": received,
            "token_mint": None,
            "error": f"Payee received {received}, expected at least {expected_amount}",
        }

    return {
        "valid": True,
        "payer": payer,
        "payee": expected_pay_to,
        "amount": received,
        "token_mint": None,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Transaction Decode / Sign (ported from moltfarm lib/signer.py)
# ---------------------------------------------------------------------------


def decode_transaction(tx_data: str) -> tuple[bytes | None, str | None]:
    """Decode a base58 or base64 encoded transaction string.

    Returns (bytes, encoding_name) or (None, None).
    """
    if not isinstance(tx_data, str) or not tx_data.strip():
        return None, None

    tx_data = tx_data.strip()
    has_b64_chars = any(c in tx_data for c in "+/=")

    # Try base64 first if it looks like base64
    if has_b64_chars:
        try:
            candidate = b64.b64decode(tx_data, validate=True)
            VersionedTransaction.from_bytes(candidate)
            return candidate, "base64"
        except Exception:
            pass

    # Try base64 without strict validation
    try:
        candidate = b64.b64decode(tx_data)
        VersionedTransaction.from_bytes(candidate)
        return candidate, "base64"
    except Exception:
        pass

    # Try base58
    try:
        candidate = base58.b58decode(tx_data)
        VersionedTransaction.from_bytes(candidate)
        return candidate, "base58"
    except Exception:
        pass

    return None, None


def sign_transaction(tx_bytes: bytes, keypair: Keypair) -> bytes:
    """Sign a VersionedTransaction, handling multi-signer cases.

    Returns signed transaction bytes.
    """
    tx = VersionedTransaction.from_bytes(tx_bytes)
    msg = tx.message
    required = msg.header.num_required_signatures
    our_pubkey = keypair.pubkey()
    existing_sigs = tx.signatures
    account_keys = msg.account_keys

    if required == 1:
        signed = VersionedTransaction(msg, [keypair])
    else:
        signers = []
        our_idx = None
        for i in range(required):
            pk = account_keys[i]
            if pk == our_pubkey:
                signers.append(keypair)
                our_idx = i
            elif i < len(existing_sigs) and existing_sigs[i] != Signature.default():
                signers.append(Presigner(pk, existing_sigs[i]))
            else:
                raise ValueError(
                    f"Missing signer at index {i}: {pk}. "
                    f"Our key ({our_pubkey}) "
                    f"{'found' if our_idx is not None else 'not yet found'}."
                )
        signed = VersionedTransaction(msg, signers)

    return bytes(signed)


async def submit_transaction(
    client: httpx.AsyncClient,
    signed_bytes: bytes,
    confirm: bool = False,
) -> dict:
    """Submit signed transaction bytes to the Solana RPC.

    Returns dict with 'success', 'signature', and optionally 'confirmed'.
    """
    signed_b58 = base58.b58encode(signed_bytes).decode()
    resp = await _rpc_post(client, "sendTransaction", [signed_b58, {"encoding": "base58"}])
    rpc = resp.json()

    if rpc.get("error"):
        raise TransactionFailedError(f"sendTransaction error: {rpc['error']}")

    sig = rpc.get("result", "")
    result = {"success": True, "signature": sig}

    if confirm and sig:
        confirmed = await confirm_transaction(client, sig)
        result["confirmed"] = confirmed

    return result


# ---------------------------------------------------------------------------
# SPL Token helpers
# ---------------------------------------------------------------------------


async def get_token_balance(client: httpx.AsyncClient, owner: str, mint: str) -> dict:
    """Get SPL token balance for a specific mint. Returns {amount, decimals, ui_amount}."""
    accounts = await get_token_accounts(client, owner)
    for account in accounts:
        if account["mint"] == mint:
            return {
                "amount": account["amount"],
                "decimals": account["decimals"],
                "ui_amount": account["ui_amount"],
            }
    return {"amount": 0, "decimals": 6, "ui_amount": 0}


async def transfer_spl_token(
    client: httpx.AsyncClient,
    from_keypair: Keypair,
    to_address: str,
    mint: str,
    amount: int,  # raw amount in token's smallest unit
    fee_lamports: int = 0,
    fee_recipient: str | None = None,
) -> str:
    """Transfer SPL tokens with optional platform fee.

    Args:
        client: HTTP client for RPC calls
        from_keypair: Sender's keypair
        to_address: Recipient's address
        mint: Token mint address
        amount: Amount in token's smallest unit (e.g., for USDC with 6 decimals, 1000000 = 1.0 USDC)
        fee_lamports: Platform fee in lamports (SOL)
        fee_recipient: Platform fee recipient address

    Returns:
        Transaction signature
    """
    from solders.instruction import Instruction
    from solders.pubkey import Pubkey
    from solders.system_program import TransferParams, transfer

    from_addr = str(from_keypair.pubkey())

    # Check SOL balance for transaction fees
    sol_balance = await get_balance(client, from_addr)
    tx_fee = 5000  # base transaction fee
    total_fee_needed = fee_lamports + tx_fee
    if sol_balance < total_fee_needed:
        raise InsufficientBalanceError(available=sol_balance, required=total_fee_needed)

    # Get sender's token account
    token_accounts = await get_token_accounts(client, from_addr)
    sender_token_account = None
    for account in token_accounts:
        if account["mint"] == mint:
            sender_token_account = account
            break

    if not sender_token_account or sender_token_account["amount"] < amount:
        available = sender_token_account["amount"] if sender_token_account else 0
        raise InsufficientBalanceError(available=available, required=amount)

    # Get or create recipient's associated token account
    Pubkey.from_string(to_address)
    Pubkey.from_string(mint)

    # Calculate associated token account address for recipient
    # Using the standard Associated Token Program formula
    Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    token_program = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

    # Find recipient's associated token account
    try:
        recipient_accounts = await get_token_accounts(client, to_address)
        for account in recipient_accounts:
            if account["mint"] == mint:
                break
    except Exception:
        pass  # Recipient might not have any token accounts yet

    # For simplicity, we'll assume the associated token account exists
    # In a production system, you'd want to check and create it if needed

    # Get sender's token account address (we need the actual account pubkey)
    sender_accounts_resp = await _rpc_post(
        client,
        "getTokenAccountsByOwner",
        [from_addr, {"mint": mint}, {"encoding": "jsonParsed"}],
    )
    sender_accounts_data = sender_accounts_resp.json()

    if not sender_accounts_data.get("result", {}).get("value"):
        raise InsufficientBalanceError(available=0, required=amount)

    sender_token_account_pubkey = Pubkey.from_string(sender_accounts_data["result"]["value"][0]["pubkey"])

    # Get recipient's token account address
    recipient_accounts_resp = await _rpc_post(
        client,
        "getTokenAccountsByOwner",
        [to_address, {"mint": mint}, {"encoding": "jsonParsed"}],
    )
    recipient_accounts_data = recipient_accounts_resp.json()

    if not recipient_accounts_data.get("result", {}).get("value"):
        raise ValueError(f"Recipient {to_address} does not have a token account for mint {mint}")

    recipient_token_account_pubkey = Pubkey.from_string(recipient_accounts_data["result"]["value"][0]["pubkey"])

    # Get blockhash
    resp = await _rpc_post(client, "getLatestBlockhash", [])
    bh_data = resp.json()
    if "error" in bh_data:
        raise RetryableError(f"Blockhash RPC error: {bh_data['error']}")
    bh = Hash.from_string(bh_data["result"]["value"]["blockhash"])

    # Build SPL token transfer instruction
    # Token transfer instruction data: opcode 3 (Transfer) + amount (8 bytes little endian)
    instruction_data = bytes([3]) + amount.to_bytes(8, byteorder="little")

    from solders.instruction import AccountMeta

    token_transfer_ix = Instruction(
        program_id=token_program,
        accounts=[
            AccountMeta(sender_token_account_pubkey, False, True),
            AccountMeta(recipient_token_account_pubkey, False, True),
            AccountMeta(from_keypair.pubkey(), True, False),
        ],
        data=instruction_data,
    )

    # Build instructions list
    instructions = [token_transfer_ix]

    # Add platform fee transfer if specified
    if fee_lamports > 0 and fee_recipient:
        instructions.append(
            transfer(
                TransferParams(
                    from_pubkey=from_keypair.pubkey(),
                    to_pubkey=Pubkey.from_string(fee_recipient),
                    lamports=fee_lamports,
                )
            )
        )

    # Build and sign transaction
    msg = Message(instructions, from_keypair.pubkey())
    tx = Transaction([from_keypair], msg, bh)
    tx_b58 = base58.b58encode(bytes(tx)).decode()

    # Send transaction
    resp = await _rpc_post(client, "sendTransaction", [tx_b58, {"encoding": "base58"}], rpc_id=2)
    result = resp.json()

    if result.get("error"):
        raise RetryableError(f"sendTransaction error: {result['error']}")

    sig = result.get("result")
    if not sig:
        raise RetryableError(f"sendTransaction returned no signature: {result}")

    logger.info(
        "spl_token_transferred",
        from_addr=from_addr[:16],
        to_addr=to_address[:16],
        mint=mint[:16],
        amount=amount,
        fee_lamports=fee_lamports,
        signature=sig[:24],
    )
    return sig


async def get_token_accounts(client: httpx.AsyncClient, owner: str) -> list[dict]:
    """Get all SPL token accounts for an owner. Returns list of {mint, amount, decimals}."""
    resp = await _rpc_post(
        client,
        "getTokenAccountsByOwner",
        [
            owner,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"},
        ],
    )
    body = resp.json()
    accounts = []
    for item in body.get("result", {}).get("value", []):
        info = item.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
        token_amount = info.get("tokenAmount", {})
        accounts.append(
            {
                "mint": info.get("mint", ""),
                "amount": int(token_amount.get("amount", "0")),
                "decimals": token_amount.get("decimals", 0),
                "ui_amount": token_amount.get("uiAmount", 0),
            }
        )
    return accounts


# ---------------------------------------------------------------------------
# SPL Mint / Associated Token Account helpers (raw instruction building)
# ---------------------------------------------------------------------------

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
ATA_PROGRAM_ID = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"
RENT_SYSVAR_ID = "SysvarRent111111111111111111111111111111111"
MINT_ACCOUNT_SPACE = 82


def associated_token_address(owner: str, mint: str) -> str:
    """Derive the Associated Token Account address for an owner+mint pair."""
    owner_pk = Pubkey.from_string(owner)
    mint_pk = Pubkey.from_string(mint)
    token_program = Pubkey.from_string(TOKEN_PROGRAM_ID)
    ata_program = Pubkey.from_string(ATA_PROGRAM_ID)
    ata, _bump = Pubkey.find_program_address(
        [bytes(owner_pk), bytes(token_program), bytes(mint_pk)], ata_program
    )
    return str(ata)


async def account_exists(client: httpx.AsyncClient, address: str) -> bool:
    """Check whether an account exists on-chain."""
    resp = await _rpc_post(client, "getAccountInfo", [address, {"encoding": "base64"}])
    body = resp.json()
    if "error" in body:
        raise RetryableError(f"RPC error: {body['error']}")
    return body.get("result", {}).get("value") is not None


async def wait_for_account(
    client: httpx.AsyncClient,
    address: str,
    timeout: float = 25.0,
) -> bool:
    """Poll until an account is visible on-chain (cross-node visibility).

    The public devnet RPC is load-balanced, so a freshly confirmed account
    may not be visible to the node serving the next simulation for a few
    seconds. Polling getAccountInfo removes that race deterministically.
    """
    import asyncio

    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if await account_exists(client, address):
            return True
        await asyncio.sleep(0.75)
    return False


async def _send_instructions(
    client: httpx.AsyncClient,
    signers: list[Keypair],
    instructions: list,
    retry_simulation: bool = False,
) -> str:
    """Build, sign and send a legacy transaction from raw instructions.

    When `retry_simulation` is True, transient simulation failures are retried
    a few times -- the public devnet RPC is load-balanced, and a transaction
    referencing an account that was just created (e.g. a new mint or token
    account) can hit a lagging node that hasn't seen it yet. A short retry
    resolves this without any code changes.
    """
    import asyncio

    attempts = 3 if retry_simulation else 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        resp = await _rpc_post(client, "getLatestBlockhash", [])
        bh_data = resp.json()
        if "error" in bh_data:
            raise RetryableError(f"Blockhash RPC error: {bh_data['error']}")
        bh = Hash.from_string(bh_data["result"]["value"]["blockhash"])

        msg = Message(instructions, signers[0].pubkey())
        tx = Transaction(signers, msg, bh)
        tx_b58 = base58.b58encode(bytes(tx)).decode()

        resp = await _rpc_post(client, "sendTransaction", [tx_b58, {"encoding": "base58"}], rpc_id=2)
        result = resp.json()
        if result.get("error"):
            last_error = RetryableError(f"sendTransaction error: {result['error']}")
            msg_text = str(last_error)
            if retry_simulation and "simulation" in msg_text and attempt < attempts - 1:
                await asyncio.sleep(1.0 + attempt)
                continue
            raise last_error
        sig = result.get("result")
        if not sig:
            raise RetryableError(f"sendTransaction returned no signature: {result}")
        return sig
    raise last_error or RetryableError("sendTransaction failed after retries")


def _create_token_account_ixs(
    funder: Pubkey,
    owner: Pubkey,
    mint: Pubkey,
    account_kp: Keypair,
    rent_lamports: int,
) -> list[Instruction]:
    """Instructions to create a brand-new token account for `owner`+`mint`.

    Uses a fresh random account (a real keypair that can sign) instead of
    the Associated Token Account program, so no PDA signature is needed:

      1. system_program.create_account   (funder -> account, rent, space 165)
      2. token_program.InitializeAccount (opcode 1)

    The account shows up in getTokenAccountsByOwner, so transfers and
    balance checks work exactly like an ATA.
    """
    from solders.instruction import AccountMeta, Instruction
    from solders.system_program import CreateAccountParams, create_account

    ix_create = create_account(
        CreateAccountParams(
            from_pubkey=funder,
            to_pubkey=account_kp.pubkey(),
            lamports=rent_lamports,
            space=165,
            owner=Pubkey.from_string(TOKEN_PROGRAM_ID),
        )
    )
    ix_init = Instruction(
        program_id=Pubkey.from_string(TOKEN_PROGRAM_ID),
        accounts=[
            AccountMeta(account_kp.pubkey(), False, True),
            AccountMeta(mint, False, False),
            AccountMeta(owner, False, False),
            AccountMeta(Pubkey.from_string(RENT_SYSVAR_ID), False, False),
        ],
        data=bytes([1]),  # InitializeAccount
    )
    return [ix_create, ix_init]


def _mint_to_ix(mint: Pubkey, dest: Pubkey, authority: Pubkey, amount_raw: int) -> Instruction:
    """Token Program MintTo (opcode 7) instruction."""
    from solders.instruction import AccountMeta, Instruction

    return Instruction(
        program_id=Pubkey.from_string(TOKEN_PROGRAM_ID),
        accounts=[
            AccountMeta(mint, False, True),
            AccountMeta(dest, False, True),
            AccountMeta(authority, True, False),
        ],
        data=bytes([7]) + amount_raw.to_bytes(8, "little"),
    )


def _init_mint_ix(mint: Pubkey, authority: Pubkey, decimals: int) -> Instruction:
    """Token Program InitializeMint (opcode 0) instruction.

    Layout: [0] opcode, [decimals], mint_authority (32 bytes), then an
    optional freeze authority COption. No `is_initialized` byte -- the
    program sets that flag on the account itself.
    """
    from solders.instruction import AccountMeta, Instruction

    return Instruction(
        program_id=Pubkey.from_string(TOKEN_PROGRAM_ID),
        accounts=[
            AccountMeta(mint, False, True),
            AccountMeta(Pubkey.from_string(RENT_SYSVAR_ID), False, False),
        ],
        data=bytes([0]) + bytes([decimals]) + bytes(authority) + bytes([0]),
    )


async def create_spl_mint(
    client: httpx.AsyncClient,
    authority_keypair: Keypair,
    decimals: int = 6,
) -> str:
    """Create a new SPL token mint owned by `authority_keypair`.

    The authority becomes the mint authority (can mint more). Returns the
    new mint address. Only the authority signs -- the mint account itself
    never needs its own key.
    """
    from solders.system_program import CreateAccountParams, create_account

    mint_kp = Keypair()
    resp = await _rpc_post(client, "getMinimumBalanceForRentExemption", [MINT_ACCOUNT_SPACE])
    rent_body = resp.json()
    if "error" in rent_body:
        raise RetryableError(f"RPC error: {rent_body['error']}")
    rent = rent_body["result"]

    instructions = [
        create_account(
            CreateAccountParams(
                from_pubkey=authority_keypair.pubkey(),
                to_pubkey=mint_kp.pubkey(),
                lamports=rent,
                space=MINT_ACCOUNT_SPACE,
                owner=Pubkey.from_string(TOKEN_PROGRAM_ID),
            )
        ),
        _init_mint_ix(mint_kp.pubkey(), authority_keypair.pubkey(), decimals),
    ]
    # solders' create_account marks the new account as a signer, so the mint
    # keypair must sign alongside the authority. Confirm before returning so
    # callers never race the mint creation (a subsequent tx that references
    # this mint would simulate before it lands and fail with IncorrectProgramId).
    sig = await _send_instructions(client, [authority_keypair, mint_kp], instructions)
    await confirm_transaction(client, sig)
    mint_addr = str(mint_kp.pubkey())
    await wait_for_account(client, mint_addr)
    return mint_addr


async def _token_account_addresses(
    client: httpx.AsyncClient, owner: str, mint: str
) -> list[str]:
    """Return the pubkeys of `owner`'s token accounts holding `mint`."""
    resp = await _rpc_post(
        client,
        "getTokenAccountsByOwner",
        [owner, {"mint": mint}, {"encoding": "jsonParsed"}],
    )
    body = resp.json()
    return [item.get("pubkey", "") for item in body.get("result", {}).get("value", [])]


async def ensure_token_account(
    client: httpx.AsyncClient,
    payer_keypair: Keypair,
    owner_address: str,
    mint: str,
) -> str:
    """Create a token account for `owner`+`mint` if missing; returns its address."""
    existing = await _token_account_addresses(client, owner_address, mint)
    if existing:
        return existing[0]

    # Rent-exempt lamports for a 165-byte token account.
    resp = await _rpc_post(client, "getMinimumBalanceForRentExemption", [165])
    rent_body = resp.json()
    if "error" in rent_body:
        raise RetryableError(f"RPC error: {rent_body['error']}")
    rent = rent_body["result"]

    account_kp = Keypair()
    ixs = _create_token_account_ixs(
        payer_keypair.pubkey(),
        Pubkey.from_string(owner_address),
        Pubkey.from_string(mint),
        account_kp,
        rent,
    )
    sig = await _send_instructions(client, [payer_keypair, account_kp], ixs, retry_simulation=True)
    # Confirm + wait for cross-node visibility so a subsequent mint_to in the
    # same flow never races the account creation (simulation would see an
    # absent account and fail with IncorrectProgramId).
    await confirm_transaction(client, sig)
    await wait_for_account(client, str(account_kp.pubkey()))
    return str(account_kp.pubkey())


async def mint_spl_token(
    client: httpx.AsyncClient,
    mint_authority_keypair: Keypair,
    mint: str,
    owner_address: str,
    amount_raw: int,
    confirm: bool = False,
) -> str:
    """Mint `amount_raw` tokens to `owner_address` (creates their ATA first).

    Returns the transaction signature. The mint authority signs; the
    recipient does not need to sign anything.
    """
    ata = await ensure_token_account(client, mint_authority_keypair, owner_address, mint)
    ix = _mint_to_ix(
        Pubkey.from_string(mint),
        Pubkey.from_string(ata),
        mint_authority_keypair.pubkey(),
        amount_raw,
    )
    sig = await _send_instructions(client, [mint_authority_keypair], [ix], retry_simulation=True)
    if confirm:
        await confirm_transaction(client, sig)
    return sig
