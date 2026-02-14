"""PDA derivation and Anchor instruction building for the AgentWallet program.

Derives PDA addresses, builds Anchor instruction discriminators, serializes
Borsh-compatible args, and constructs Solana instructions for the on-chain
program at CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6.
"""

import hashlib
import struct

import httpx
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from .config import get_settings
from .exceptions import RetryableError
from .logging import get_logger
from .retry import retry

logger = get_logger(__name__)

PROGRAM_ID = Pubkey.from_string("CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6")
SYSTEM_PROGRAM = Pubkey.from_string("11111111111111111111111111111111")


# ---------------------------------------------------------------------------
# Anchor discriminator
# ---------------------------------------------------------------------------


def _anchor_discriminator(name: str) -> bytes:
    """Compute 8-byte Anchor instruction discriminator: sha256("global:<name>")[:8]."""
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]


# ---------------------------------------------------------------------------
# Borsh serialization helpers
# ---------------------------------------------------------------------------


def _encode_u64(value: int) -> bytes:
    return struct.pack("<Q", value)


def _encode_i64(value: int) -> bytes:
    return struct.pack("<q", value)


def _encode_string(s: str) -> bytes:
    encoded = s.encode("utf-8")
    return struct.pack("<I", len(encoded)) + encoded


def _encode_bool(value: bool) -> bytes:
    return b"\x01" if value else b"\x00"


# ---------------------------------------------------------------------------
# PDA derivation
# ---------------------------------------------------------------------------


def derive_pda(org_pubkey: Pubkey, agent_id_seed: str) -> tuple[Pubkey, int]:
    """Derive the AgentWallet PDA address from org pubkey and agent id seed.

    Returns (pda_address, bump).
    """
    pda, bump = Pubkey.find_program_address(
        [b"agent_wallet", bytes(org_pubkey), agent_id_seed.encode()],
        PROGRAM_ID,
    )
    return pda, bump


def derive_platform_config_pda() -> tuple[Pubkey, int]:
    """Derive the platform config PDA."""
    pda, bump = Pubkey.find_program_address(
        [b"platform_config"],
        PROGRAM_ID,
    )
    return pda, bump


# ---------------------------------------------------------------------------
# Instruction builders
# ---------------------------------------------------------------------------


def build_create_agent_wallet_ix(
    authority: Pubkey,
    org_pubkey: Pubkey,
    agent_id_seed: str,
    spending_limit_per_tx: int,
    daily_limit: int,
) -> tuple[Instruction, Pubkey, int]:
    """Build the create_agent_wallet instruction.

    Returns (instruction, pda_address, bump).
    """
    pda, bump = derive_pda(org_pubkey, agent_id_seed)

    data = (
        _anchor_discriminator("create_agent_wallet")
        + _encode_string(agent_id_seed)
        + _encode_u64(spending_limit_per_tx)
        + _encode_u64(daily_limit)
    )

    accounts = [
        AccountMeta(authority, is_signer=True, is_writable=True),
        AccountMeta(org_pubkey, is_signer=False, is_writable=False),
        AccountMeta(pda, is_signer=False, is_writable=True),
        AccountMeta(SYSTEM_PROGRAM, is_signer=False, is_writable=False),
    ]

    ix = Instruction(PROGRAM_ID, data, accounts)
    return ix, pda, bump


def build_transfer_with_limit_ix(
    authority: Pubkey,
    agent_wallet_pda: Pubkey,
    recipient: Pubkey,
    amount: int,
    fee_wallet: Pubkey | None = None,
) -> Instruction:
    """Build the transfer_with_limit instruction."""
    platform_config_pda, _ = derive_platform_config_pda()

    if fee_wallet is None:
        settings = get_settings()
        fee_wallet_str = settings.platform_wallet_address
        if fee_wallet_str:
            fee_wallet = Pubkey.from_string(fee_wallet_str)
        else:
            fee_wallet = SYSTEM_PROGRAM

    data = _anchor_discriminator("transfer_with_limit") + _encode_u64(amount)

    accounts = [
        AccountMeta(authority, is_signer=True, is_writable=True),
        AccountMeta(agent_wallet_pda, is_signer=False, is_writable=True),
        AccountMeta(platform_config_pda, is_signer=False, is_writable=False),
        AccountMeta(fee_wallet, is_signer=False, is_writable=True),
        AccountMeta(recipient, is_signer=False, is_writable=True),
        AccountMeta(SYSTEM_PROGRAM, is_signer=False, is_writable=False),
    ]

    return Instruction(PROGRAM_ID, data, accounts)


def build_update_limits_ix(
    authority: Pubkey,
    agent_wallet_pda: Pubkey,
    spending_limit_per_tx: int,
    daily_limit: int,
    is_active: bool,
) -> Instruction:
    """Build the update_limits instruction."""
    data = (
        _anchor_discriminator("update_limits")
        + _encode_u64(spending_limit_per_tx)
        + _encode_u64(daily_limit)
        + _encode_bool(is_active)
    )

    accounts = [
        AccountMeta(authority, is_signer=True, is_writable=False),
        AccountMeta(agent_wallet_pda, is_signer=False, is_writable=True),
    ]

    return Instruction(PROGRAM_ID, data, accounts)


# ---------------------------------------------------------------------------
# On-chain state deserialization
# ---------------------------------------------------------------------------


def deserialize_agent_wallet_state(data: bytes) -> dict:
    """Deserialize AgentWallet account data (after 8-byte Anchor discriminator).

    Layout:
      authority: 32 bytes (Pubkey)
      org: 32 bytes (Pubkey)
      agent_id: 4-byte length + UTF-8 string
      spending_limit_per_tx: 8 bytes (u64 LE)
      daily_limit: 8 bytes (u64 LE)
      daily_spent: 8 bytes (u64 LE)
      last_reset_day: 8 bytes (i64 LE)
      is_active: 1 byte (bool)
      bump: 1 byte (u8)
    """
    offset = 8  # skip discriminator

    authority = Pubkey.from_bytes(data[offset : offset + 32])
    offset += 32

    org = Pubkey.from_bytes(data[offset : offset + 32])
    offset += 32

    agent_id_len = struct.unpack("<I", data[offset : offset + 4])[0]
    offset += 4
    agent_id = data[offset : offset + agent_id_len].decode("utf-8")
    offset += agent_id_len

    spending_limit_per_tx = struct.unpack("<Q", data[offset : offset + 8])[0]
    offset += 8

    daily_limit = struct.unpack("<Q", data[offset : offset + 8])[0]
    offset += 8

    daily_spent = struct.unpack("<Q", data[offset : offset + 8])[0]
    offset += 8

    last_reset_day = struct.unpack("<q", data[offset : offset + 8])[0]
    offset += 8

    is_active = data[offset] == 1
    offset += 1

    bump = data[offset]

    return {
        "authority": str(authority),
        "org": str(org),
        "agent_id": agent_id,
        "spending_limit_per_tx": spending_limit_per_tx,
        "daily_limit": daily_limit,
        "daily_spent": daily_spent,
        "last_reset_day": last_reset_day,
        "is_active": is_active,
        "bump": bump,
    }


# ---------------------------------------------------------------------------
# RPC helpers for reading PDA state
# ---------------------------------------------------------------------------


def _rpc_url() -> str:
    return get_settings().solana_rpc_url


def _rpc_timeout() -> int:
    return get_settings().rpc_timeout


@retry()
async def get_pda_account_info(client: httpx.AsyncClient, pda_address: str) -> dict | None:
    """Fetch and deserialize a PDA account's on-chain state.

    Returns deserialized state dict or None if account doesn't exist.
    """
    import base64 as b64

    resp = await client.post(
        _rpc_url(),
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [pda_address, {"encoding": "base64"}],
        },
        timeout=_rpc_timeout(),
    )
    resp.raise_for_status()
    body = resp.json()

    if "error" in body:
        raise RetryableError(f"RPC error: {body['error']}")

    result = body.get("result")
    if result is None:
        raise RetryableError("RPC returned no result")

    value = result.get("value")
    if value is None:
        return None  # account doesn't exist

    account_data = value.get("data")
    if not account_data or not isinstance(account_data, list) or len(account_data) < 1:
        return None

    raw_data = b64.b64decode(account_data[0])
    return deserialize_agent_wallet_state(raw_data)
