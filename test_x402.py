"""Test script for x402 implementation."""

import asyncio
import json
from agentwallet.packages.sdk_python.src.agentwallet import AgentWallet, X402AutoPay


async def test_x402():
    """Test x402 integration."""
    
    # Initialize AgentWallet client
    async with AgentWallet(api_key="test_key") as aw:
        print("✅ AgentWallet client initialized")
        print(f"✅ x402 resource available: {hasattr(aw, 'x402')}")
        
        # Test discovery (this won't actually work without a real x402 endpoint)
        try:
            payment_info = await aw.x402.discover("https://httpbin.org/status/402")
            print(f"✅ Discovery method works: {payment_info}")
        except Exception as e:
            print(f"ℹ️  Discovery test failed (expected): {e}")
        
        # Test middleware initialization
        try:
            async with X402AutoPay(
                wallet_id="test_wallet",
                aw_client=aw,
                max_per_request=0.01
            ) as client:
                print("✅ X402AutoPay middleware initialized")
                print(f"✅ Payment history: {client.get_payment_history()}")
                print(f"✅ Total spent: ${client.get_total_spent()}")
        except Exception as e:
            print(f"❌ Middleware test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_x402())