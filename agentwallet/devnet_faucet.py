#!/usr/bin/env python
"""Deterministic devnet faucet — funds an address from the platform keypair.

The public devnet faucets are IP rate-limited, so tests that need on-chain
funding (smoke test escrow/transfer, escrow lifecycle, x402 lifecycle) fall
back to this: it signs a real SOL transfer with the platform wallet, which
is the same custody wallet that pays escrow releases/refunds.

Usage:
    python devnet_faucet.py <address> <lamports> [--rpc URL]

Run from the repo root (packages/api/.platform-keypair.json is relative),
or set PLATFORM_PRIVATE_KEY_HEX to override the key.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from solders.hash import Hash
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

RPC = "https://api.devnet.solana.com"


def load_platform_keypair() -> Keypair:
    hex_key = os.environ.get("PLATFORM_PRIVATE_KEY_HEX", "")
    if not hex_key:
        keyfile = Path("packages/api/.platform-keypair.json")
        if keyfile.exists():
            hex_key = json.loads(keyfile.read_text()).get("secret_key_hex", "")
    if not hex_key:
        raise SystemExit(
            "No platform key: set PLATFORM_PRIVATE_KEY_HEX or place "
            "packages/api/.platform-keypair.json"
        )
    return Keypair.from_bytes(bytes.fromhex(hex_key))


async def fund(address: str, lamports: int, rpc: str) -> str:
    kp = load_platform_keypair()
    async with httpx.AsyncClient(timeout=30) as client:
        # Latest blockhash
        resp = await client.post(
            rpc,
            json={"jsonrpc": "2.0", "id": 1, "method": "getLatestBlockhash"},
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise SystemExit(f"blockhash error: {data['error']}")
        bh = Hash.from_string(data["result"]["value"]["blockhash"])

        # Build + sign transfer
        ix = transfer(
            TransferParams(
                from_pubkey=kp.pubkey(),
                to_pubkey=Pubkey.from_string(address),
                lamports=lamports,
            )
        )
        msg = Message([ix], kp.pubkey())
        tx = Transaction([kp], msg, bh)
        from base58 import b58encode

        tx_b58 = b58encode(bytes(tx)).decode()

        # Send
        resp = await client.post(
            rpc,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "sendTransaction",
                "params": [tx_b58, {"encoding": "base58", "preflightCommitment": "confirmed"}],
            },
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise SystemExit(f"sendTransaction error: {result['error']}")
        sig = result.get("result")
        if not sig:
            raise SystemExit(f"sendTransaction returned no signature: {result}")

        # Confirm
        for _ in range(20):
            await asyncio.sleep(2)
            r = await client.post(
                rpc,
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "getSignatureStatuses",
                    "params": [[sig], {"searchTransactionHistory": True}],
                },
            )
            statuses = (r.json().get("result") or {}).get("value") or []
            if statuses and statuses[0] and statuses[0].get("confirmationStatus") in (
                "confirmed",
                "finalized",
            ):
                return sig
        return sig  # best effort — polled 40s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("address")
    ap.add_argument("lamports", type=int)
    ap.add_argument("--rpc", default=RPC)
    args = ap.parse_args()

    sig = asyncio.run(fund(args.address, args.lamports, args.rpc))
    print(f"funded {args.address} with {args.lamports} lamports — {sig}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
