"""Tweet with retry on rate limit"""
import sys
import time
sys.path.insert(0, r'C:\Users\black\Desktop\agentwallet\scripts')
from tweet import get_client
import os

def tweet_with_retry(text, image_path, max_retries=5):
    client, api_v1 = get_client()
    
    # Upload media first
    media_ids = []
    if image_path and os.path.exists(image_path):
        print(f"[UPLOAD] {image_path}", flush=True)
        media = api_v1.media_upload(filename=image_path)
        media_ids = [media.media_id]
        print(f"[OK] Media ID: {media.media_id}", flush=True)
    
    # Try posting with retry
    for attempt in range(max_retries):
        try:
            print(f"[POST attempt {attempt+1}] {text[:60]}...", flush=True)
            kwargs = {"text": text}
            if media_ids:
                kwargs["media_ids"] = media_ids
            response = client.create_tweet(**kwargs)
            tweet_id = response.data["id"]
            url = f"https://x.com/Web3__Youth/status/{tweet_id}"
            print(f"[OK] {url}", flush=True)
            return url
        except Exception as e:
            if "429" in str(e) or "Too Many" in str(e):
                wait = 180 * (attempt + 1)  # 3min, 6min, 9min...
                print(f"[RATE LIMITED] Waiting {wait}s before retry...", flush=True)
                time.sleep(wait)
            else:
                print(f"[ERROR] {e}", flush=True)
                raise
    
    print("[FAILED] Max retries exceeded", flush=True)
    return None

if __name__ == "__main__":
    text = sys.argv[1]
    img = sys.argv[2]
    result = tweet_with_retry(text, img)
    print(f"RESULT: {result}", flush=True)
