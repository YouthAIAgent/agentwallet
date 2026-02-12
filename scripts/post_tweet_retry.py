import sys, time, os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, r'C:\Users\black\Desktop\agentwallet\scripts')

# Use tweepy directly with retry logic
import json, tweepy

with open(r'C:\Users\black\.openclaw\secrets\twitter-api.json') as f:
    keys = json.load(f)

auth = tweepy.OAuth1UserHandler(
    keys['consumer_key'], keys['consumer_secret'],
    keys['access_token'], keys['access_token_secret']
)
api = tweepy.API(auth)
client = tweepy.Client(
    consumer_key=keys['consumer_key'],
    consumer_secret=keys['consumer_secret'],
    access_token=keys['access_token'],
    access_token_secret=keys['access_token_secret']
)

tweet_text = """Built AgentWallet on Anchor PDAs \u2014 every AI agent gets a deterministic vault. No private keys floating around, just program-derived addresses.

27 MCP tools. Solana-native. @armani\u2019s framework made this real.

pip install agentwallet-mcp
agentwallet.fun

#Solana #Anchor #Web3"""

img_path = r'C:\Users\black\.openclaw\media\browser\6965f171-9c50-4e07-a639-576ba3bab28a.png'

# Upload media
media = api.media_upload(filename=img_path)
print(f"[OK] Media ID: {media.media_id}")

# Retry loop
for attempt in range(5):
    try:
        response = client.create_tweet(text=tweet_text, media_ids=[media.media_id], user_auth=True)
        tweet_id = response.data['id']
        print(f"[POSTED] https://twitter.com/Web3__Youth/status/{tweet_id}")
        break
    except tweepy.errors.TooManyRequests as e:
        wait = 120 * (attempt + 1)
        print(f"[RATE LIMITED] Attempt {attempt+1}/5. Waiting {wait}s...")
        time.sleep(wait)
    except Exception as e:
        print(f"[ERROR] {e}")
        break
else:
    print("[FAILED] All retry attempts exhausted. Rate limit still active.")
