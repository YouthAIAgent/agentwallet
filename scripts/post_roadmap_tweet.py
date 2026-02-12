import tweepy, json

SECRETS_PATH = r"C:\Users\black\.openclaw\secrets\twitter-api.json"
with open(SECRETS_PATH) as f:
    creds = json.load(f)

auth = tweepy.OAuth1UserHandler(
    creds["consumer_key"],
    creds["consumer_secret"],
    creds["access_token"],
    creds["access_token_secret"]
)
api_v1 = tweepy.API(auth)

client = tweepy.Client(
    consumer_key=creds["consumer_key"],
    consumer_secret=creds["consumer_secret"],
    access_token=creds["access_token"],
    access_token_secret=creds["access_token_secret"]
)

image_path = r"C:\Users\black\Desktop\agentwallet\tweet-cards\roadmap-card.png"
media = api_v1.media_upload(filename=image_path)
print(f"Media ID: {media.media_id}")

tweet_text = """AgentWallet Protocol — 2026 Roadmap.

Q1 (DONE):
- Anchor program deployed on devnet
- Python SDK on PyPI
- 33 MCP tools
- Security audit shipped
- $AGENTPRO live on DEX Screener

Q2 (NOW):
- Solana mainnet
- x402 HTTP payments
- Agent reputation system
- TypeScript SDK

Q3-Q4:
- Multi-chain (Base, Arbitrum)
- Agent marketplace
- ML anomaly detection

We don't announce roadmaps. We ship them.

agentwallet.fun

#Solana #AI #BuildInPublic"""

response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
tid = response.data["id"]
print(f"Tweet ID: {tid}")
print(f"URL: https://x.com/Web3__Youth/status/{tid}")
