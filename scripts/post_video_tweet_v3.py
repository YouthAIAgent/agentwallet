"""Post a tweet with 2min trimmed video"""
import json
import os
import sys
import time
import math
import requests
from requests_oauthlib import OAuth1
import tweepy

SECRETS_PATH = r"C:\Users\black\.openclaw\secrets\twitter-api.json"

with open(SECRETS_PATH) as f:
    creds = json.load(f)

oauth = OAuth1(
    creds["consumer_key"], creds["consumer_secret"],
    creds["access_token"], creds["access_token_secret"]
)

UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"

video_path = r"C:\Users\black\Desktop\agentwallet\promo-video\out\full-explainer-2min.mp4"
total_bytes = os.path.getsize(video_path)
print(f"File: {total_bytes} bytes ({total_bytes/1024/1024:.1f} MB)", flush=True)

# INIT
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

# APPEND
CHUNK_SIZE = 4 * 1024 * 1024
num_chunks = math.ceil(total_bytes / CHUNK_SIZE)
print(f"Uploading {num_chunks} chunk(s)...", flush=True)
with open(video_path, "rb") as f:
    for i in range(num_chunks):
        chunk = f.read(CHUNK_SIZE)
        print(f"  Chunk {i} ({len(chunk)} bytes)...", flush=True)
        r = requests.post(UPLOAD_URL, data={
            "command": "APPEND",
            "media_id": media_id,
            "segment_index": i
        }, files={"media": chunk}, auth=oauth)
        print(f"  APPEND: {r.status_code}", flush=True)

# FINALIZE
print("FINALIZE...", flush=True)
r = requests.post(UPLOAD_URL, data={
    "command": "FINALIZE",
    "media_id": media_id
}, auth=oauth)
result = r.json()
print(f"FINALIZE: {r.status_code} - state: {result.get('processing_info', {}).get('state', 'done')}", flush=True)

# Wait for processing
if "processing_info" in result:
    state = result["processing_info"]["state"]
    while state in ["pending", "in_progress"]:
        wait = result["processing_info"].get("check_after_secs", 5)
        print(f"Processing ({state})... waiting {wait}s", flush=True)
        time.sleep(max(wait, 2))
        r = requests.get(UPLOAD_URL, params={
            "command": "STATUS",
            "media_id": media_id
        }, auth=oauth)
        result = r.json()
        pinfo = result.get("processing_info", {})
        state = pinfo.get("state", "succeeded")
        pct = pinfo.get("progress_percent", "?")
        print(f"  {state} - {pct}%", flush=True)
    if state == "failed":
        print(f"FAILED: {result}", flush=True)
        sys.exit(1)

print("Video ready! Tweeting...", flush=True)

client = tweepy.Client(
    consumer_key=creds["consumer_key"],
    consumer_secret=creds["consumer_secret"],
    access_token=creds["access_token"],
    access_token_secret=creds["access_token_secret"]
)

tweet_text = """AI agents need wallets. Not custodial, not multisig — self-custodial wallets where the agent IS the owner.

AgentWallet uses Solana PDAs → deterministic wallets per agent. No private keys. No human bottleneck. Agent signs its own txns.

How it works:
→ PDA derived from agent's unique ID
→ Program validates identity on-chain
→ Autonomous execution, full audit trail

Every AI framework is hacking hot wallets with exposed keys. That's not infra — that's a liability.

We built the wallet layer agents deserve.

agentwallet.fun

@toly @armani @0xMert_ @jessepollak @balajis @solana @base"""

response = client.create_tweet(text=tweet_text, media_ids=[media_id])
tweet_id = response.data["id"]
print(f"DONE: https://x.com/Web3__Youth/status/{tweet_id}", flush=True)
