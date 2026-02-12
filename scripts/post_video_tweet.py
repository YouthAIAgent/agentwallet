"""Post a tweet with video attachment"""
import tweepy
import json
import os
import sys
import time

SECRETS_PATH = r"C:\Users\black\.openclaw\secrets\twitter-api.json"

with open(SECRETS_PATH) as f:
    creds = json.load(f)

auth = tweepy.OAuth1UserHandler(
    creds["consumer_key"],
    creds["consumer_secret"],
    creds["access_token"],
    creds["access_token_secret"]
)
api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
client = tweepy.Client(
    consumer_key=creds["consumer_key"],
    consumer_secret=creds["consumer_secret"],
    access_token=creds["access_token"],
    access_token_secret=creds["access_token_secret"]
)

video_path = r"C:\Users\black\Desktop\agentwallet\promo-video\out\full-explainer-tg.mp4"
fsize = os.path.getsize(video_path)
print(f"File: {fsize} bytes ({fsize/1024/1024:.1f} MB)", flush=True)

tweet_text = """AI agents need wallets. Not custodial, not multisig — true self-custodial wallets where the agent IS the owner.

AgentWallet uses Solana PDAs to give every AI agent its own deterministic wallet. No private keys to leak. No human bottleneck.

→ PDA derived from agent's unique ID
→ Program authority validates identity
→ Autonomous transaction execution
→ Full on-chain audit trail

Every AI framework needs on-chain txns. Hot wallets with exposed keys aren't infra — they're a liability.

We're building the wallet layer agents deserve.

agentwallet.fun

@toly @armani @0xMert_ @jessepollak @balajis @solana @base"""

try:
    print("Uploading video (chunked)...", flush=True)
    media = api_v1.media_upload(
        filename=video_path,
        media_category="tweet_video",
        chunked=True,
        wait_for_async_finalize=True
    )
    media_id = media.media_id
    print(f"Upload complete! Media ID: {media_id}", flush=True)
    
    print("Posting tweet with video...", flush=True)
    response = client.create_tweet(text=tweet_text, media_ids=[media_id])
    tweet_id = response.data["id"]
    print(f"DONE: https://x.com/Web3__Youth/status/{tweet_id}", flush=True)

except Exception as e:
    print(f"Video upload failed: {e}", flush=True)
    print("Posting text-only as fallback...", flush=True)
    try:
        response = client.create_tweet(text=tweet_text)
        tweet_id = response.data["id"]
        print(f"TEXT-ONLY: https://x.com/Web3__Youth/status/{tweet_id}", flush=True)
    except Exception as e2:
        print(f"Text tweet also failed: {e2}", flush=True)
