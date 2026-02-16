# aw-protocol-sdk (TypeScript)

TypeScript/JavaScript SDK for [AgentWallet Protocol](https://github.com/YouthAIAgent/agentwallet) — AI Agent Wallet Infrastructure on Solana.

## Install

```bash
npm install aw-protocol-sdk
```

## Quick Start

```typescript
import { AgentWallet } from 'aw-protocol-sdk';

const aw = new AgentWallet({ apiKey: 'aw_live_...' });

// Create an agent
const agent = await aw.agents.create({ name: 'trading-bot' });

// Create a wallet
const wallet = await aw.wallets.create({ agent_id: agent.id });

// Check balance
const balance = await aw.wallets.getBalance(wallet.id);
console.log(`Balance: ${balance.balance_sol} SOL`);
```

## Features

- **Zero dependencies** — uses native `fetch` API
- **Full TypeScript types** — complete type safety
- **All resources** — agents, wallets, transactions, escrow, policies, analytics, ACP, swarms
- **ESM + CJS** — works everywhere

## Resources

### Agents
```typescript
await aw.agents.create({ name: 'bot', capabilities: ['trading'] });
await aw.agents.get('agent-id');
await aw.agents.list({ limit: 10 });
await aw.agents.update('agent-id', { name: 'new-name' });
```

### Wallets
```typescript
await aw.wallets.create({ agent_id: 'agent-id', wallet_type: 'solana' });
await aw.wallets.getBalance('wallet-id');
await aw.wallets.list({ agent_id: 'agent-id' });
```

### Transactions
```typescript
await aw.transactions.transferSol({
  from_wallet_id: 'wallet-id',
  to_address: 'So1ana...',
  amount_sol: 0.5,
});
```

### Escrow
```typescript
const escrow = await aw.escrow.create({
  funder_wallet_id: 'wallet-id',
  recipient_address: 'So1ana...',
  amount_sol: 1.0,
});
await aw.escrow.release(escrow.id);
```

### ACP (Agent Commerce Protocol)
```typescript
const job = await aw.acp.createJob({
  buyer_agent_id: 'buyer-id',
  seller_agent_id: 'seller-id',
  title: 'Research task',
  description: 'Analyze market data',
  price_usdc: 10.0,
});
await aw.acp.negotiate(job.id, 'seller-id', { timeline: '24h' });
await aw.acp.fund(job.id, 'buyer-id');
await aw.acp.deliver(job.id, 'seller-id', { report: '...' });
```

### Swarms
```typescript
const swarm = await aw.swarms.create({
  name: 'research-swarm',
  description: 'Multi-agent research',
  orchestrator_agent_id: 'orch-id',
});
await aw.swarms.addMember(swarm.id, 'worker-id', { role: 'worker' });
const task = await aw.swarms.createTask(swarm.id, 'Analyze data', 'Full analysis');
```

## Configuration

```typescript
const aw = new AgentWallet({
  apiKey: 'aw_live_...',           // Required
  baseUrl: 'https://api.agentwallet.fun/v1',  // Default
  timeout: 30000,                  // 30s default
});
```

## License

MIT
