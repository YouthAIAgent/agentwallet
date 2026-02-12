"""Quick retry script with backoff for rate-limited tweets"""
import sys, json, time, tweepy

SECRETS_PATH = r"C:\Users\black\.openclaw\secrets\twitter-api.json"

def post():
    with open(SECRETS_PATH) as f:
        creds = json.load(f)
    
    client = tweepy.Client(
        consumer_key=creds["consumer_key"],
        consumer_secret=creds["consumer_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"]
    )
    
    auth = tweepy.OAuth1UserHandler(
        creds["consumer_key"], creds["consumer_secret"],
        creds["access_token"], creds["access_token_secret"]
    )
    api_v1 = tweepy.API(auth)
    
    text = sys.argv[1]
    image_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    media_ids = []
    if image_path:
        import os
        if os.path.exists(image_path):
            print(f"[UPLOAD] {image_path}")
            media = api_v1.media_upload(filename=image_path)
            media_ids = [media.media_id]
            print(f"[OK] Media ID: {media.media_id}")
    
    kwargs = {"text": text}
    if media_ids:
        kwargs["media_ids"] = media_ids
    
    for attempt in range(5):
        try:
            print(f"[ATTEMPT {attempt+1}] Posting...")
            response = client.create_tweet(**kwargs)
            tweet_id = response.data["id"]
            url = f"https://x.com/Web3__Youth/status/{tweet_id}"
            print(f"[OK] {url}")
            return url
        except tweepy.errors.TooManyRequests as e:
            wait = 60 * (attempt + 1)
            print(f"[RATE LIMITED] Waiting {wait}s...")
            time.sleep(wait)
    
    print("[FAILED] All retries exhausted")
    return None

if __name__ == "__main__":
    post()
