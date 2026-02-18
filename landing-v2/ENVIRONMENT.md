# AgentWallet dApp - Environment Configuration

## Overview
This document outlines the required environment variables for deploying and running the AgentWallet dApp.

## Required Environment Variables

### Solana Connection
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_SOLANA_NETWORK` | Solana cluster to connect to | `devnet` | ✅ |
| `VITE_SOLANA_RPC_URL` | RPC endpoint URL | `https://api.devnet.solana.com` | ✅ |
| `VITE_SOLANA_WS_URL` | WebSocket endpoint for real-time updates | `wss://api.devnet.solana.com` | ❌ |

### Program IDs
| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `VITE_AGENT_WALLET_PROGRAM_ID` | Deployed program ID on devnet | `11111111111111111111111111111111` | ✅ |
| `VITE_TOKEN_PROGRAM_ID` | SPL Token program ID | `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` | ❌ |
| `VITE_ASSOCIATED_TOKEN_PROGRAM_ID` | Associated token account program | `ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL` | ❌ |

### API Keys (Optional - Production Recommended)
| Variable | Description | Provider | Required |
|----------|-------------|----------|----------|
| `VITE_HELIUS_API_KEY` | Enhanced RPC via Helius | helius.xyz | ❌ |
| `VITE_HELIUS_RPC_URL` | Custom Helius RPC endpoint | helius.xyz | ❌ |
| `VITE_QUICKNODE_RPC_URL` | QuickNode RPC endpoint | quicknode.com | ❌ |

### Wallet Adapter
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_WALLET_ADAPTER_NETWORK` | Wallet adapter network | `Devnet` | ✅ |

### Feature Flags
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_ENABLE_DEV_TOOLS` | Enable developer tools | `false` | ❌ |
| `VITE_ENABLE_ANALYTICS` | Enable analytics tracking | `false` | ❌ |
| `VITE_DEBUG_MODE` | Enable debug logging | `false` | ❌ |

## Environment File Templates

### Development (`.env.development`)
```env
# Solana Configuration
VITE_SOLANA_NETWORK=devnet
VITE_SOLANA_RPC_URL=https://api.devnet.solana.com
VITE_SOLANA_WS_URL=wss://api.devnet.solana.com

# Program IDs
VITE_AGENT_WALLET_PROGRAM_ID=your_program_id_here
VITE_TOKEN_PROGRAM_ID=TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
VITE_ASSOCIATED_TOKEN_PROGRAM_ID=ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL

# Wallet Adapter
VITE_WALLET_ADAPTER_NETWORK=Devnet

# Development Features
VITE_ENABLE_DEV_TOOLS=true
VITE_DEBUG_MODE=true
```

### Production (`.env.production`)
```env
# Solana Configuration - Switch to mainnet for production
VITE_SOLANA_NETWORK=mainnet-beta
VITE_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
VITE_SOLANA_WS_URL=wss://api.mainnet-beta.solana.com

# Program IDs
VITE_AGENT_WALLET_PROGRAM_ID=your_mainnet_program_id_here
VITE_TOKEN_PROGRAM_ID=TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
VITE_ASSOCIATED_TOKEN_PROGRAM_ID=ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL

# Wallet Adapter
VITE_WALLET_ADAPTER_NETWORK=Mainnet

# Production Settings
VITE_ENABLE_DEV_TOOLS=false
VITE_ENABLE_ANALYTICS=true
VITE_DEBUG_MODE=false
```

## GitHub Secrets Required

Configure these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel authentication token |
| `VERCEL_ORG_ID` | Your Vercel organization ID |
| `VERCEL_PROJECT_ID_LANDING` | Project ID for the landing page |
| `AGENT_WALLET_PROGRAM_ID` | Deployed program ID |

## Getting Vercel Credentials

1. **Vercel Token**: Go to [Vercel Settings → Tokens](https://vercel.com/account/tokens) and create a new token
2. **Org ID**: Run `vercel teams list` or find it in your Vercel dashboard URL
3. **Project ID**: Run `vercel project list` or check `.vercel/project.json`

## RPC Provider Recommendations

### Free Public RPC (Development)
- **Endpoint**: `https://api.devnet.solana.com`
- **Rate Limit**: ~100 req/10s per IP
- **Use Case**: Development, testing

### Helius (Recommended)
- **Signup**: https://helius.xyz
- **Features**: Enhanced APIs, webhooks, higher rate limits
- **Free Tier**: Available for development

### QuickNode
- **Signup**: https://quicknode.com
- **Features**: Dedicated endpoints, archive nodes
- **Free Tier**: Available for development

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `.env` files containing real keys
- Use GitHub Secrets for CI/CD pipelines
- Rotate API keys regularly
- Use dedicated RPC endpoints for production
- Enable IP allowlisting on RPC providers when possible

## Deployment Checklist

- [ ] Set all required environment variables
- [ ] Configure GitHub Secrets
- [ ] Verify RPC endpoint connectivity
- [ ] Test wallet connection on devnet
- [ ] Confirm Program ID is deployed and matches
- [ ] Enable HTTPS enforcement on Vercel
- [ ] Test CSP headers don't block wallet popups
- [ ] Verify CORS settings for API calls
