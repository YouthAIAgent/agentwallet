# x402 HTTP-Native Payments Integration

This document describes AgentWallet's integration with [x402](https://www.x402.org), an open standard for HTTP-native payments that enables AI agents to automatically pay for API access with stablecoins.

## What is x402?

x402 is an open standard that allows servers to require payment for API access by responding with `HTTP 402 Payment Required` along with JSON describing accepted payment methods. Clients can then automatically pay and retry the request.

This eliminates the need for:
- Creating accounts with each API provider
- Managing API keys and subscriptions
- Prepaying for credits that may go unused
- Complex billing and payment flows

## Quick Start

### Basic Usage

```python
import asyncio
from agentwallet import AgentWallet

async def main():
    async with AgentWallet(api_key="aw_live_...") as aw:
        # Make request that auto-pays if 402 received
        response = await aw.x402.pay_and_fetch(
            url="https://api.example.com/premium-data",
            wallet_id="wallet_123",
            max_amount_usd=0.05,  # Max $0.05 per request
        )
        
        if response.payment_required:
            print(f"Paid ${response.cost_usd:.4f} automatically")
            print(f"Transaction: {response.payment_proof.signature}")
        
        print("Data:", response.data)

asyncio.run(main())
```

### Auto-Payment Middleware

For seamless integration, use the middleware that automatically handles all 402 responses:

```python
from agentwallet import AgentWallet, X402AutoPay

async def main():
    async with AgentWallet(api_key="aw_live_...") as aw:
        async with X402AutoPay(
            wallet_id="wallet_123",
            aw_client=aw,
            max_per_request=0.01,
        ) as client:
            # Use like any HTTP client - payments happen automatically
            response = await client.get("https://api.example.com/data")
            data = response.json()
            
            # Check payment history
            print(f"Total spent: ${client.get_total_spent()}")
```

## API Reference

### X402Resource

The main x402 client integrated into AgentWallet:

#### `pay_and_fetch(url, method="GET", wallet_id=None, max_amount_usd=None, **kwargs)`

Make an HTTP request that automatically pays if 402 Payment Required is received.

**Parameters:**
- `url`: Target URL
- `method`: HTTP method (GET, POST, etc.)
- `wallet_id`: AgentWallet wallet ID for payments
- `max_amount_usd`: Maximum USD amount willing to pay
- `**kwargs`: Additional arguments for HTTP request

**Returns:** `X402Response` with status, data, and payment info

#### `discover(url)`

Probe an endpoint to check if it supports x402 payments without paying.

**Returns:** `X402PaymentInfo` or `None`

#### `estimate(url, method="GET")`

Estimate the cost of accessing an x402 endpoint without paying.

**Returns:** Estimated cost in USD as `float`

### X402AutoPay

Middleware that wraps httpx client to automatically handle 402 responses.

```python
client = X402AutoPay(
    wallet_id="wallet_123",
    aw_client=aw,
    max_per_request=0.10,  # Max $0.10 per request
)
```

**Methods:** `get()`, `post()`, `put()`, `patch()`, `delete()`, `head()`, `options()`

**Additional methods:**
- `get_payment_history()`: Returns list of all payments made
- `get_total_spent()`: Returns total USD spent
- `close()`: Clean up resources

### X402Budget

Budget management for controlling x402 spending:

```python
from agentwallet import X402Budget

budget = X402Budget(
    daily_limit=1.00,      # Max $1.00 per day
    per_request_limit=0.05 # Max $0.05 per request
)

if budget.can_afford(estimated_cost):
    # Make payment
    budget.record_payment(actual_cost)
```

## Response Format

The x402 standard defines this JSON format for 402 responses:

```json
{
  "x402Version": "1.0",
  "description": "Premium weather data access",
  "accepts": [
    {
      "network": "solana",
      "token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      "amount": "1000",
      "payTo": "11111111111111111111111111111112"
    },
    {
      "network": "base-sepolia", 
      "token": "0xa0b86a33e6776e681c0d7d5a52f7bd17c2bec3f0",
      "amount": "1000000",
      "payTo": "0x742d35cc6634c0532925a3b8d78dbeebff8300c9"
    }
  ]
}
```

## Payment Method Selection

AgentWallet automatically selects the best payment method based on this priority:

1. **Solana USDC** (highest preference)
2. **Other Solana stablecoins** (USDT)
3. **Solana SOL**
4. **Other Solana SPL tokens**
5. **Other blockchain networks**

The selection also considers your budget limits and available wallet balance.

## Error Handling

Common errors and how to handle them:

```python
from agentwallet.exceptions import AgentWalletAPIError

try:
    response = await aw.x402.pay_and_fetch(url, wallet_id="...", max_amount_usd=0.01)
except AgentWalletAPIError as e:
    if e.status_code == 402:
        if "exceeds max" in e.message:
            print("Payment amount too high for budget")
        elif "No acceptable payment method" in e.message:
            print("Unsupported payment method (need Solana USDC?)")
        elif "insufficient balance" in e.message:
            print("Wallet balance too low")
    else:
        print(f"API error: {e.message}")
```

## Security and Limits

### Budget Controls

Always set reasonable budget limits to prevent runaway spending:

```python
# Per-request limit
response = await aw.x402.pay_and_fetch(
    url=url,
    wallet_id=wallet_id,
    max_amount_usd=0.05  # Never pay more than $0.05
)

# Daily budget tracking
budget = X402Budget(daily_limit=1.00)
if budget.can_afford(estimated_cost):
    # Make payment
    pass
```

### Audit Trail

All payments are logged for audit purposes:

```python
# With middleware
async with X402AutoPay(...) as client:
    # Make requests...
    
    # Get audit trail
    payments = client.get_payment_history()
    for payment in payments:
        print(f"Paid ${payment['amount_usd']} to {payment['url']}")
        print(f"  Signature: {payment['signature']}")
```

### Wallet Security

- Use dedicated wallets for x402 payments with limited balances
- Monitor payment activity regularly
- Set appropriate daily/request limits

## Integration Examples

See `examples/x402_usage.py` for comprehensive examples including:

- Basic manual payment handling
- Automatic payment middleware
- Budget management
- Error handling
- Multi-network support
- Discovery and cost estimation

## Supported Networks

Current implementation supports:

- **Solana** (preferred) - SOL, USDC, USDT, other SPL tokens
- **Base Sepolia** - ETH, USDC, ERC-20 tokens
- Extensible for other networks supported by AgentWallet

## Contributing

To extend x402 support:

1. Add network support in `_execute_payment()` method
2. Update `_estimate_cost_usd()` with pricing logic
3. Modify `_score_payment_option()` for network preferences
4. Test with real x402-enabled endpoints

## Learn More

- [x402 Standard](https://www.x402.org) - Official specification
- [AgentWallet Documentation](../../../README.md) - Core wallet functionality
- [Examples](../../../examples/x402_usage.py) - Working code examples