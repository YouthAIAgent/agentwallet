import tweepy, json, time

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

CARDS_DIR = r"C:\Users\black\Desktop\agentwallet\tweet-cards"

thread = [
    {
        "text": "Why AI agents need their own wallets — and why we built one on Solana.\n\nA thread on AgentWallet Protocol.\n\n33 MCP tools. 7 Anchor instructions. 15K+ lines of code. 166 token holders.\n\nFrom problem to production. Here's the full story.\n\nagentwallet.fun\n\n🧵👇",
        "image": f"{CARDS_DIR}\\article-card-1.png"
    },
    {
        "text": "1/ THE PROBLEM\n\nAI agents are managing billions with zero financial infrastructure.\n\n• No spending limits — one compromised agent drains everything\n• Private keys sitting in .env files\n• No agent-to-agent escrow\n• Zero audit trail\n• No compliance framework\n\nHuman wallets weren't built for this.",
        "image": f"{CARDS_DIR}\\article-card-2.png"
    },
    {
        "text": "2/ THE ARCHITECTURE\n\n3-layer stack, each doing one thing well:\n\nPython SDK → FastAPI Backend → Solana Anchor Program\n\n• SDK: Stripe-like async client, 7 resources\n• API: 12 routers, policy engine on every tx, 7 workers\n• On-chain: 3 PDAs — AgentWallet, EscrowAccount, PlatformConfig\n\nAll open source. All audited.",
        "image": f"{CARDS_DIR}\\article-card-3.png"
    },
    {
        "text": "3/ THE CODE\n\nNot pseudocode. Real production code.\n\nPython SDK — 3 lines to give your AI agent a Solana wallet:\n  pip install aw-protocol-sdk\n\nAnchor program — PDA derivation with checked arithmetic, spend limits, escrow closing.\n\nEvery line is on GitHub. MIT licensed.\n\ngithub.com/YouthAIAgent/agentwallet",
        "image": f"{CARDS_DIR}\\article-card-4.png"
    },
    {
        "text": "4/ WHY IT MATTERS\n\nHuman wallets vs Agent-native wallets:\n\n❌ No limits → ✅ Per-tx + daily caps\n❌ Manual escrow → ✅ On-chain PDA\n❌ No audit → ✅ Immutable log\n❌ .env keys → ✅ Encrypted (KMS)\n❌ Shared wallet → ✅ Dedicated PDA per agent\n❌ Zero tools → ✅ 33 MCP tools\n❌ No compliance → ✅ EU AI Act ready",
        "image": f"{CARDS_DIR}\\article-card-5.png"
    },
    {
        "text": "5/ WHAT'S NEXT\n\nAgentWallet is competing in the @colosseum Agent Hackathon.\n\n$AGENTPRO — community token now live on DEX Screener with Enhanced Token Info.\n\nWe ship code. The community grows because the product is real.\n\nVote: colosseum.com/agent-hackathon/projects/agentwallet-protocol\n\nagentwallet.fun\n\n#Solana #AI #BuildInPublic",
        "image": f"{CARDS_DIR}\\article-card-6.png"
    }
]

last_tweet_id = None

for i, t in enumerate(thread):
    # Upload image
    media = api_v1.media_upload(filename=t["image"])
    print(f"[{i+1}/6] Media uploaded: {media.media_id}")
    
    kwargs = {
        "text": t["text"],
        "media_ids": [media.media_id]
    }
    
    if last_tweet_id:
        kwargs["in_reply_to_tweet_id"] = last_tweet_id
    
    response = client.create_tweet(**kwargs)
    last_tweet_id = response.data["id"]
    url = f"https://x.com/Web3__Youth/status/{last_tweet_id}"
    print(f"[{i+1}/6] Posted: {url}")
    
    if i < len(thread) - 1:
        time.sleep(3)

print(f"\nThread complete! First tweet: https://x.com/Web3__Youth/status/{thread[0].get('_id', last_tweet_id)}")
