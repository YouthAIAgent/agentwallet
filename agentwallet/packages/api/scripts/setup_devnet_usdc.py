"""Create a devnet USDC (dUSDC) mint for the billing demo.

The AgentWallet platform mints its own devnet stablecoin (dUSDC, 6 decimals)
so the USDC billing demo can run end to end on devnet without depending on
Circle's devnet faucet. The platform keypair becomes the mint authority, so
the playground "Get USDC" endpoint can mint grants to any user wallet.

Run once against devnet (uses the local platform keypair):

    python -m scripts.setup_devnet_usdc

Then set the printed mint address as USDC_MINT_ADDRESS on the API (Railway):

    railway variables --service api --set USDC_MINT_ADDRESS=<mint>
"""

import asyncio
import json
from pathlib import Path

import httpx
from agentwallet.core import solana
from agentwallet.core.config import get_settings

INITIAL_SUPPLY = 1_000_000  # 1,000,000 dUSDC to the platform wallet


def _platform_keypair():
    hex_key = get_settings().platform_private_key_hex
    if not hex_key:
        candidates = [
            Path("packages/api/.platform-keypair.json"),
            Path(".platform-keypair.json"),
            Path(__file__).resolve().parent.parent / ".platform-keypair.json",
        ]
        for keyfile in candidates:
            if keyfile.exists():
                try:
                    hex_key = json.loads(keyfile.read_text()).get("secret_key_hex", "")
                except Exception:
                    hex_key = ""
                if hex_key:
                    break
    if not hex_key:
        raise SystemExit(
            "No platform keypair found -- set PLATFORM_PRIVATE_KEY_HEX or place packages/api/.platform-keypair.json"
        )
    return solana.Keypair.from_bytes(bytes.fromhex(hex_key))


async def main():
    kp = _platform_keypair()
    platform = str(kp.pubkey())
    print(f"platform: {platform}")

    async with httpx.AsyncClient(timeout=30) as client:
        bal = await solana.get_balance(client, platform)
        print(f"platform SOL: {bal / 1e9:.4f}")
        if bal < 30_000_000:  # ~0.03 SOL for rent + fees
            raise SystemExit("Platform wallet is low on devnet SOL -- fund it first.")

        print("creating dUSDC mint (6 decimals)...")
        mint = await solana.create_spl_mint(client, kp, decimals=6)
        print(f"mint: {mint}")

        print("creating platform ATA + minting initial supply...")
        sig = await solana.mint_spl_token(
            client,
            kp,
            mint,
            platform,
            INITIAL_SUPPLY * (10**6),
            confirm=True,
        )
        print(f"initial supply signature: {sig}")

        ata = solana.associated_token_address(platform, mint)
        print(f"platform ATA: {ata}")

    print()
    print("=== SET THIS ENV VAR ON THE API (Railway) ===")
    print(f"USDC_MINT_ADDRESS={mint}")


if __name__ == "__main__":
    asyncio.run(main())
