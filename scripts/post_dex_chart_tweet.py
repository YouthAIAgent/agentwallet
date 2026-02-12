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

image_path = r"C:\Users\black\.openclaw\media\inbound\file_25---3f51eed7-097f-43a4-939d-83e028012bf0.jpg"
media = api_v1.media_upload(filename=image_path)
print(f"Media ID: {media.media_id}")

tweet_text = """$AGENTPRO just went live on DEX Screener with full Enhanced Token Info.

166 holders. Real volume. Real builders behind it.

This isn't another token with a whitepaper and a dream.

Behind $AGENTPRO there's a deployed Solana program, a published Python SDK, 33 MCP tools, and a full-stack dashboard.

We ship code. The chart follows.

CA: B8r3Yp5C2Kx5fAyCLVMoVaGoiQkAaqzLsh69adDGBAGS

agentwallet.fun

#Solana #AGENTPRO #AI #BuildInPublic"""

response = client.create_tweet(text=tweet_text, media_ids=[media.media_id])
tid = response.data["id"]
print(f"Tweet ID: {tid}")
print(f"URL: https://x.com/Web3__Youth/status/{tid}")
