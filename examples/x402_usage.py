"""
x402 HTTP-native Payment Examples
=================================

Examples showing how to use AgentWallet's x402 integration for automatic
HTTP-native payments when encountering 402 Payment Required responses.

x402 is an open standard that allows servers to require payment for API access,
and clients to automatically pay with stablecoins and retry the request.
"""

import asyncio
import logging
from agentwallet import AgentWallet, X402AutoPay, X402Budget

# Configure logging to see payment activity
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_x402_usage():
    """Basic example: Manual x402 payment handling."""
    
    async with AgentWallet(api_key="aw_live_your_key_here") as aw:
        try:
            # Try to access a paid API endpoint
            response = await aw.x402.pay_and_fetch(
                url="https://api.example.com/premium-weather",
                wallet_id="wallet_abc123",
                max_amount_usd=0.05,  # Maximum $0.05 per request
            )
            
            if response.payment_required:
                logger.info(f"✅ Paid ${response.cost_usd:.4f} automatically")
                logger.info(f"Transaction: {response.payment_proof.signature}")
            
            print("Weather data:", response.data)
            
        except Exception as e:
            logger.error(f"Request failed: {e}")


async def example_auto_payment_middleware():
    """Example: Automatic payment middleware for seamless API access."""
    
    async with AgentWallet(api_key="aw_live_your_key_here") as aw:
        
        # Create auto-paying HTTP client
        async with X402AutoPay(
            wallet_id="wallet_abc123",
            aw_client=aw,
            max_per_request=0.01,  # Max $0.01 per request
        ) as client:
            
            # Use like a regular HTTP client - payments happen automatically
            response = await client.get("https://api.example.com/premium-data")
            data = response.json()
            
            # Check payment history
            payments = client.get_payment_history()
            total_spent = client.get_total_spent()
            
            logger.info(f"Made {len(payments)} payments, total: ${total_spent:.4f}")
            for payment in payments:
                logger.info(f"  - ${payment['amount_usd']:.4f} to {payment['url']}")


async def example_discovery_and_estimation():
    """Example: Discover x402 support and estimate costs."""
    
    async with AgentWallet(api_key="aw_live_your_key_here") as aw:
        
        urls = [
            "https://api.example.com/free-endpoint",
            "https://api.example.com/paid-endpoint",
            "https://api.premium-service.com/data",
        ]
        
        for url in urls:
            # Check if endpoint supports x402 payments
            payment_info = await aw.x402.discover(url)
            
            if payment_info:
                # Estimate cost
                estimated_cost = await aw.x402.estimate(url)
                logger.info(f"🔒 {url}")
                logger.info(f"   Description: {payment_info.description}")
                logger.info(f"   Estimated cost: ${estimated_cost:.4f}")
                logger.info(f"   Payment options: {len(payment_info.accepts)}")
            else:
                logger.info(f"🆓 {url} - Free access")


async def example_budget_management():
    """Example: Budget management for x402 payments."""
    
    # Create budget with daily and per-request limits
    budget = X402Budget(
        daily_limit=1.00,      # Max $1.00 per day
        per_request_limit=0.05 # Max $0.05 per request
    )
    
    async with AgentWallet(api_key="aw_live_your_key_here") as aw:
        
        api_calls = [
            "https://api.example.com/call1",
            "https://api.example.com/call2", 
            "https://api.example.com/call3",
        ]
        
        for url in api_calls:
            # Check budget before making request
            estimated_cost = await aw.x402.estimate(url)
            
            if budget.can_afford(estimated_cost):
                try:
                    response = await aw.x402.pay_and_fetch(
                        url=url,
                        wallet_id="wallet_abc123",
                        max_amount_usd=budget.per_request_limit,
                    )
                    
                    if response.payment_required:
                        budget.record_payment(response.cost_usd)
                        logger.info(f"✅ Paid ${response.cost_usd:.4f} for {url}")
                        logger.info(f"   Remaining budget: ${budget.get_remaining_daily():.4f}")
                    
                    # Use response.data...
                    
                except Exception as e:
                    logger.error(f"Failed to access {url}: {e}")
            else:
                logger.warning(f"⏸️  Skipping {url} - exceeds budget (${estimated_cost:.4f})")


async def example_error_handling():
    """Example: Robust error handling for x402 payments."""
    
    async with AgentWallet(api_key="aw_live_your_key_here") as aw:
        
        try:
            response = await aw.x402.pay_and_fetch(
                url="https://api.expensive.com/data",
                wallet_id="wallet_abc123",
                max_amount_usd=0.01,  # Low budget
            )
            
        except Exception as e:
            error_msg = str(e)
            
            if "exceeds max" in error_msg:
                logger.error("💸 Payment amount too high for our budget")
            elif "insufficient balance" in error_msg:
                logger.error("💳 Insufficient wallet balance")
            elif "Payment execution failed" in error_msg:
                logger.error("❌ Payment transaction failed")
            elif "No acceptable payment method found" in error_msg:
                logger.error("🚫 No supported payment method (need Solana USDC?)")
            else:
                logger.error(f"🔥 Unexpected error: {error_msg}")


async def example_multi_network_support():
    """Example: Shows support for multiple blockchain networks."""
    
    async with AgentWallet(api_key="aw_live_your_key_here") as aw:
        
        # The x402 implementation automatically selects the best payment method:
        # 1. Prefers Solana USDC (highest score)
        # 2. Falls back to other Solana tokens (SOL, other SPL tokens)  
        # 3. Supports other networks if no Solana option available
        
        response = await aw.x402.pay_and_fetch(
            url="https://api.multi-chain.com/data",
            wallet_id="wallet_abc123",
            max_amount_usd=0.10,
        )
        
        if response.payment_required:
            proof = response.payment_proof
            logger.info(f"✅ Paid with {proof.network} {proof.token}")
            logger.info(f"   Transaction: {proof.signature}")
            logger.info(f"   Amount: {proof.amount} (${response.cost_usd:.4f} USD)")


if __name__ == "__main__":
    print("🚀 AgentWallet x402 Payment Examples")
    print("====================================")
    
    # Run examples (comment out the ones you don't want to test)
    # Note: These examples won't work without valid API keys and x402-enabled endpoints
    
    # asyncio.run(example_basic_x402_usage())
    # asyncio.run(example_auto_payment_middleware()) 
    # asyncio.run(example_discovery_and_estimation())
    # asyncio.run(example_budget_management())
    # asyncio.run(example_error_handling())
    # asyncio.run(example_multi_network_support())
    
    print("📚 See the examples above for different x402 usage patterns")
    print("💡 Replace 'aw_live_your_key_here' with your actual AgentWallet API key")
    print("🔗 Learn more about x402: https://www.x402.org")