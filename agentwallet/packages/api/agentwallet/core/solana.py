"""Solana RPC operations -- ported from moltfarm lib/wallet.py and lib/signer.py.

Provides: balance queries, SOL/SPL transfers, transaction signing,
confirmation polling, and decode utilities.
"""

import base64 as b64

import base58
import httpx
from solders.hash import Hash
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


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


@retry()
async def get_balance(client: httpx.AsyncClient, address: str) -> int:
    """Get SOL balance in lamports. Raises RetryableError on RPC failure."""
    resp = await client.post(
        _rpc_url(),
        json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]},
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
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
    resp = await client.post(
        _rpc_url(),
        json={"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash"},
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    bh_data = resp.json()
    if "error" in bh_data:
        raise RetryableError(f"Blockhash RPC error: {bh_data['error']}")
    bh = Hash.from_string(bh_data["result"]["value"]["blockhash"])

    # Build instructions
    instructions = [
        transfer(TransferParams(
            from_pubkey=from_keypair.pubkey(),
            to_pubkey=Pubkey.from_string(to_address),
            lamports=lamports,
        ))
    ]

    if fee_lamports > 0 and fee_recipient:
        instructions.append(
            transfer(TransferParams(
                from_pubkey=from_keypair.pubkey(),
                to_pubkey=Pubkey.from_string(fee_recipient),
                lamports=fee_lamports,
            ))
        )

    msg = Message(instructions, from_keypair.pubkey())
    tx = Transaction([from_keypair], msg, bh)
    tx_b58 = base58.b58encode(bytes(tx)).decode()

    # Send
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "sendTransaction",
            "params": [tx_b58, {"encoding": "base58"}],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
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
            resp = await client.post(
                _rpc_url(),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignatureStatuses",
                    "params": [[signature], {"searchTransactionHistory": True}],
                },
                timeout=_rpc_timeout(),
            )
            resp.raise_for_status()
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
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [signed_b58, {"encoding": "base58"}],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
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


async def get_token_balance(
    client: httpx.AsyncClient, owner: str, mint: str
) -> dict:
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
    recipient_pubkey = Pubkey.from_string(to_address)
    mint_pubkey = Pubkey.from_string(mint)
    
    # Calculate associated token account address for recipient
    # Using the standard Associated Token Program formula
    associated_token_program = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    token_program = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    
    # Find recipient's associated token account
    recipient_token_account = None
    try:
        recipient_accounts = await get_token_accounts(client, to_address)
        for account in recipient_accounts:
            if account["mint"] == mint:
                recipient_token_account = account
                break
    except:
        pass  # Recipient might not have any token accounts yet
    
    # For simplicity, we'll assume the associated token account exists
    # In a production system, you'd want to check and create it if needed
    
    # Get sender's token account address (we need the actual account pubkey)
    sender_accounts_resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                from_addr,
                {"mint": mint},
                {"encoding": "jsonParsed"},
            ],
        },
        timeout=_rpc_timeout(),
    )
    sender_accounts_resp.raise_for_status()
    sender_accounts_data = sender_accounts_resp.json()
    
    if not sender_accounts_data.get("result", {}).get("value"):
        raise InsufficientBalanceError(available=0, required=amount)
    
    sender_token_account_pubkey = Pubkey.from_string(
        sender_accounts_data["result"]["value"][0]["pubkey"]
    )
    
    # Get recipient's token account address
    recipient_accounts_resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                to_address,
                {"mint": mint},
                {"encoding": "jsonParsed"},
            ],
        },
        timeout=_rpc_timeout(),
    )
    recipient_accounts_resp.raise_for_status()
    recipient_accounts_data = recipient_accounts_resp.json()
    
    if not recipient_accounts_data.get("result", {}).get("value"):
        raise ValueError(f"Recipient {to_address} does not have a token account for mint {mint}")
    
    recipient_token_account_pubkey = Pubkey.from_string(
        recipient_accounts_data["result"]["value"][0]["pubkey"]
    )
    
    # Get blockhash
    resp = await client.post(
        _rpc_url(),
        json={"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash"},
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    bh_data = resp.json()
    if "error" in bh_data:
        raise RetryableError(f"Blockhash RPC error: {bh_data['error']}")
    bh = Hash.from_string(bh_data["result"]["value"]["blockhash"])
    
    # Build SPL token transfer instruction
    # Token transfer instruction data: [1, amount (8 bytes little endian)]
    instruction_data = bytes([1]) + amount.to_bytes(8, byteorder='little')
    
    token_transfer_ix = Instruction(
        program_id=token_program,
        accounts=[
            {"pubkey": sender_token_account_pubkey, "is_signer": False, "is_writable": True},
            {"pubkey": recipient_token_account_pubkey, "is_signer": False, "is_writable": True},
            {"pubkey": from_keypair.pubkey(), "is_signer": True, "is_writable": False},
        ],
        data=instruction_data,
    )
    
    # Build instructions list
    instructions = [token_transfer_ix]
    
    # Add platform fee transfer if specified
    if fee_lamports > 0 and fee_recipient:
        instructions.append(
            transfer(TransferParams(
                from_pubkey=from_keypair.pubkey(),
                to_pubkey=Pubkey.from_string(fee_recipient),
                lamports=fee_lamports,
            ))
        )
    
    # Build and sign transaction
    msg = Message(instructions, from_keypair.pubkey())
    tx = Transaction([from_keypair], msg, bh)
    tx_b58 = base58.b58encode(bytes(tx)).decode()
    
    # Send transaction
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "sendTransaction",
            "params": [tx_b58, {"encoding": "base58"}],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
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


async def get_token_accounts(
    client: httpx.AsyncClient, owner: str
) -> list[dict]:
    """Get all SPL token accounts for an owner. Returns list of {mint, amount, decimals}."""
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                owner,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()
    accounts = []
    for item in body.get("result", {}).get("value", []):
        info = item.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
        token_amount = info.get("tokenAmount", {})
        accounts.append({
            "mint": info.get("mint", ""),
            "amount": int(token_amount.get("amount", "0")),
            "decimals": token_amount.get("decimals", 0),
            "ui_amount": token_amount.get("uiAmount", 0),
        })
    return accounts
