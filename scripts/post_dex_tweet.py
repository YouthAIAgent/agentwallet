import tweepy, json, os

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

# Upload the DEX Screener screenshot
image_path = r"C:\Users\black\.openclaw\media\inbound\file_24---bcad6269-3986-416d-96cc-deee13742261.jpg"
media = api_v1.media_upload(filename=image_path)
print(f"Media ID: {media.media_id}")

tweet_text = """Just paid $299 for Enhanced Token Info on DEX Screener.

$AGENTPRO is getting the full treatment.

Not a meme. Not a fundraiser. A community token backing real open-source AI infrastructure on Solana.

33 MCP tools. 7 Anchor instructions. PDA wallets for AI agents.

The code is public. The product is live.

agentwallet.fun

@0xMert_ #Solana #AI #BuildInPublic"""

response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
tid = response.data["id"]
print(f"Tweet ID: {tid}")
print(f"URL: https://x.com/Web3__Youth/status/{tid}")
