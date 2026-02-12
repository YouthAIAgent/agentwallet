"""
AgentWallet Twitter Engine v2.0
Professional content creation + image generation + API posting
"""
import tweepy
import json
import sys
import os
import random
import time
import io

# Fix Unicode output on Windows (cp1252 breaks on emojis)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SECRETS_PATH = r"C:\Users\black\.openclaw\secrets\twitter-api.json"

def get_client():
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
    
    return client, api_v1

def tweet_with_image(text, image_path=None):
    """Post a tweet with optional image or video"""
    client, api_v1 = get_client()
    
    media_ids = []
    if image_path and os.path.exists(image_path):
        print(f"[UPLOAD] {image_path}")
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.mp4', '.mov', '.avi']:
            media = api_v1.media_upload(
                filename=image_path,
                media_category='tweet_video',
                chunked=True
            )
            print(f"[VIDEO] Processing media ID: {media.media_id}")
        else:
            media = api_v1.media_upload(filename=image_path)
        media_ids = [media.media_id]
        print(f"[OK] Media ID: {media.media_id}")
    
    print(f"[POST] {text[:80]}...")
    
    kwargs = {"text": text}
    if media_ids:
        kwargs["media_ids"] = media_ids
    
    response = client.create_tweet(**kwargs)
    tweet_id = response.data["id"]
    url = f"https://x.com/Web3__Youth/status/{tweet_id}"
    
    print(f"[OK] {url}")
    return url

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tweet.py <text> [image_path]")
        sys.exit(1)
    text = sys.argv[1]
    image = sys.argv[2] if len(sys.argv) > 2 else None
    tweet_with_image(text, image)
