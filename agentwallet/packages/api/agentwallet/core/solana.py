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
# SPL Token helpers (stub for Phase 2)
# ---------------------------------------------------------------------------


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
