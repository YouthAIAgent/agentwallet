"""EVM RPC operations for ERC-8004 identity & reputation.

Mirrors core/solana.py pattern: uses httpx for JSON-RPC, web3 for ABI encoding only.
"""

import asyncio

import httpx

from .config import get_settings
from .exceptions import EVMTransactionError, RetryableError
from .logging import get_logger
from .retry import retry

logger = get_logger(__name__)

try:
    from eth_account import Account
    from eth_account.signers.local import LocalAccount
    from web3 import Web3

    _HAS_WEB3 = True
except ImportError:
    _HAS_WEB3 = False
    Web3 = None  # type: ignore
    Account = None  # type: ignore
    LocalAccount = None  # type: ignore
    logger.warning("web3/eth-account not installed — EVM features disabled")

# ---------------------------------------------------------------------------
# ERC-8004 ABI fragments (only the functions we call)
# ---------------------------------------------------------------------------

IDENTITY_ABI = [
    {
        "name": "registerAgent",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "name", "type": "string"},
            {"name": "metadataURI", "type": "string"},
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}],
    },
    {
        "name": "getAgentIdentity",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "outputs": [
            {"name": "name", "type": "string"},
            {"name": "metadataURI", "type": "string"},
            {"name": "owner", "type": "address"},
        ],
    },
    {
        "name": "tokenOfOwnerByIndex",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "index", "type": "uint256"},
        ],
        "outputs": [{"name": "tokenId", "type": "uint256"}],
    },
]

REPUTATION_ABI = [
    {
        "name": "submitFeedback",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "agentId", "type": "uint256"},
            {"name": "rating", "type": "uint8"},
            {"name": "comment", "type": "string"},
        ],
        "outputs": [],
    },
    {
        "name": "getReputation",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "outputs": [
            {"name": "score", "type": "uint256"},
            {"name": "feedbackCount", "type": "uint256"},
        ],
    },
]

# Shared web3 instance (used for ABI encoding only, no provider needed)
_w3 = Web3() if _HAS_WEB3 else None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rpc_url() -> str:
    return get_settings().evm_rpc_url


def _rpc_timeout() -> int:
    return get_settings().rpc_timeout


# ---------------------------------------------------------------------------
# ABI Encoding / Decoding
# ---------------------------------------------------------------------------


def encode_function_call(abi: list[dict], fn_name: str, args: list) -> str:
    """ABI-encode a function call. Returns hex-encoded calldata."""
    contract = _w3.eth.contract(abi=abi)
    return contract.encode_abi(fn_name=fn_name, args=args)


def decode_function_result(abi: list[dict], fn_name: str, data: str) -> tuple:
    """ABI-decode a function return value."""
    output_types = [o["type"] for o in next(a for a in abi if a.get("name") == fn_name)["outputs"]]
    return _w3.codec.decode(output_types, bytes.fromhex(data.removeprefix("0x")))


# ---------------------------------------------------------------------------
# JSON-RPC calls via httpx
# ---------------------------------------------------------------------------


@retry(max_attempts=3)
async def eth_call(
    client: httpx.AsyncClient,
    to: str,
    data: str,
    block: str = "latest",
) -> str:
    """Read-only eth_call. Returns hex result."""
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [{"to": to, "data": data}, block],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RetryableError(f"eth_call error: {body['error']}")
    return body.get("result", "0x")


@retry(max_attempts=3)
async def send_raw_transaction(client: httpx.AsyncClient, signed_tx: str) -> str:
    """Submit a signed transaction. Returns tx hash."""
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_sendRawTransaction",
            "params": [signed_tx],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise EVMTransactionError(f"eth_sendRawTransaction error: {body['error']}")
    tx_hash = body.get("result")
    if not tx_hash:
        raise EVMTransactionError(f"No tx hash returned: {body}")
    logger.info("evm_tx_sent", tx_hash=tx_hash[:18])
    return tx_hash


async def get_transaction_receipt(
    client: httpx.AsyncClient,
    tx_hash: str,
    max_polls: int = 20,
    poll_interval: float = 2.0,
) -> dict | None:
    """Poll for transaction receipt. Returns receipt dict or None on timeout."""
    for _ in range(max_polls):
        try:
            resp = await client.post(
                _rpc_url(),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                },
                timeout=_rpc_timeout(),
            )
            resp.raise_for_status()
            body = resp.json()
            receipt = body.get("result")
            if receipt is not None:
                status = int(receipt.get("status", "0x0"), 16)
                if status == 1:
                    logger.info("evm_tx_confirmed", tx_hash=tx_hash[:18])
                else:
                    logger.error("evm_tx_reverted", tx_hash=tx_hash[:18])
                return receipt
        except Exception as e:
            logger.warning("evm_receipt_poll_error", error=str(e))
        await asyncio.sleep(poll_interval)

    logger.warning("evm_tx_receipt_timeout", tx_hash=tx_hash[:18])
    return None


async def _get_nonce(client: httpx.AsyncClient, address: str) -> int:
    """Get the next nonce for an address."""
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getTransactionCount",
            "params": [address, "latest"],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RetryableError(f"eth_getTransactionCount error: {body['error']}")
    return int(body["result"], 16)


async def _get_gas_price(client: httpx.AsyncClient) -> int:
    """Get current gas price in wei."""
    resp = await client.post(
        _rpc_url(),
        json={"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice", "params": []},
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise RetryableError(f"eth_gasPrice error: {body['error']}")
    return int(body["result"], 16)


async def _estimate_gas(client: httpx.AsyncClient, tx: dict) -> int:
    """Estimate gas for a transaction."""
    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_estimateGas",
            "params": [tx],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()
    if "error" in body:
        raise EVMTransactionError(f"eth_estimateGas error: {body['error']}")
    return int(body["result"], 16)


# ---------------------------------------------------------------------------
# Transaction Building
# ---------------------------------------------------------------------------


async def build_and_sign_tx(
    client: httpx.AsyncClient,
    private_key: str,
    to: str,
    data: str,
    chain_id: int | None = None,
    value: int = 0,
) -> str:
    """Build, sign, and return raw transaction hex.

    Uses the platform private key to sign ERC-8004 registration/feedback calls.
    """
    settings = get_settings()
    chain_id = chain_id or settings.evm_chain_id

    account: LocalAccount = Account.from_key(private_key)
    sender = account.address

    nonce = await _get_nonce(client, sender)
    gas_price = await _get_gas_price(client)

    # Estimate gas
    tx_for_estimate = {
        "from": sender,
        "to": to,
        "data": data,
        "value": hex(value),
    }
    gas_limit = await _estimate_gas(client, tx_for_estimate)
    # Add 20% buffer
    gas_limit = int(gas_limit * 1.2)

    tx = {
        "nonce": nonce,
        "gasPrice": gas_price,
        "gas": gas_limit,
        "to": Web3.to_checksum_address(to),
        "value": value,
        "data": data,
        "chainId": chain_id,
    }

    signed = account.sign_transaction(tx)
    raw_hex = signed.raw_transaction.hex()
    return raw_hex if raw_hex.startswith("0x") else f"0x{raw_hex}"
