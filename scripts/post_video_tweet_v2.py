"""Post a tweet with video - manual chunked upload"""
import json
import os
import sys
import time
import math
import requests
from requests_oauthlib import OAuth1

SECRETS_PATH = r"C:\Users\black\.openclaw\secrets\twitter-api.json"

with open(SECRETS_PATH) as f:
    creds = json.load(f)

oauth = OAuth1(
    creds["consumer_key"], creds["consumer_secret"],
    creds["access_token"], creds["access_token_secret"]
)

UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
TWEET_URL = "https://api.twitter.com/2/tweets"

video_path = r"C:\Users\black\Desktop\agentwallet\promo-video\out\full-explainer-tg.mp4"
total_bytes = os.path.getsize(video_path)
print(f"File: {total_bytes} bytes ({total_bytes/1024/1024:.1f} MB)", flush=True)

# Step 1: INIT
print("INIT...", flush=True)
r = requests.post(UPLOAD_URL, data={
    "command": "INIT",
    "media_type": "video/mp4",
    "total_bytes": total_bytes,
    "media_category": "tweet_video"
}, auth=oauth)
print(f"INIT: {r.status_code}", flush=True)
if r.status_code not in [200, 201, 202]:
    print(f"INIT failed: {r.text}", flush=True)
    sys.exit(1)

media_id = r.json()["media_id_string"]
print(f"Media ID: {media_id}", flush=True)

# Step 2: APPEND (chunked)
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks
num_chunks = math.ceil(total_bytes / CHUNK_SIZE)
print(f"Uploading {num_chunks} chunk(s)...", flush=True)

with open(video_path, "rb") as f:
    for i in range(num_chunks):
        chunk = f.read(CHUNK_SIZE)
        print(f"  Chunk {i}/{num_chunks-1} ({len(chunk)} bytes)...", flush=True)
        r = requests.post(UPLOAD_URL, data={
            "command": "APPEND",
            "media_id": media_id,
            "segment_index": i
        }, files={"media": chunk}, auth=oauth)
        print(f"  APPEND: {r.status_code}", flush=True)
        if r.status_code not in [200, 201, 202, 204]:
            print(f"  APPEND failed: {r.text}", flush=True)
            sys.exit(1)

# Step 3: FINALIZE
print("FINALIZE...", flush=True)
r = requests.post(UPLOAD_URL, data={
    "command": "FINALIZE",
    "media_id": media_id
}, auth=oauth)
print(f"FINALIZE: {r.status_code}", flush=True)
result = r.json()
print(f"FINALIZE response: {json.dumps(result, indent=2)}", flush=True)

# Step 4: Check processing status
if "processing_info" in result:
    state = result["processing_info"]["state"]
    while state in ["pending", "in_progress"]:
        wait = result["processing_info"].get("check_after_secs", 5)
        print(f"Processing: {state}, waiting {wait}s...", flush=True)
        time.sleep(wait)
        r = requests.get(UPLOAD_URL, params={
            "command": "STATUS",
            "media_id": media_id
        }, auth=oauth)
        result = r.json()
        print(f"STATUS: {json.dumps(result.get('processing_info', {}))}", flush=True)
        state = result.get("processing_info", {}).get("state", "succeeded")
    
    if state == "failed":
        print(f"Processing FAILED: {result}", flush=True)
        sys.exit(1)

print("Video ready! Posting tweet...", flush=True)

# Step 5: Post tweet with video
import tweepy
client = tweepy.Client(
    consumer_key=creds["consumer_key"],
    consumer_secret=creds["consumer_secret"],
    access_token=creds["access_token"],
    access_token_secret=creds["access_token_secret"]
)

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

response = client.create_tweet(text=tweet_text, media_ids=[media_id])
tweet_id = response.data["id"]
print(f"DONE: https://x.com/Web3__Youth/status/{tweet_id}", flush=True)
