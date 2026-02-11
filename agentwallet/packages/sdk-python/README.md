# aw-protocol-sdk

Python SDK for the AgentWallet Protocol — AI Agent Wallet Infrastructure on Solana.

## Install

```bash
pip install aw-protocol-sdk
```

## Quick Start

```python
from agentwallet import AgentWallet

async with AgentWallet(api_key="aw_live_...") as aw:
    agent = await aw.agents.create(name="trading-bot")
    tx = await aw.transactions.transfer_sol(
        from_wallet=agent["default_wallet_id"],
        to_address="RecipientPubkey...",
        amount_sol=0.5,
    )
```

## Links

- [GitHub](https://github.com/YouthAIAgent/agentwallet)
- [API Docs](https://trustworthy-celebration-production-6a3e.up.railway.app/docs)
