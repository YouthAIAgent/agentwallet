"""
Capture landing page frames using CDP screenshots + stitch to MP4/GIF
Uses Pillow for GIF creation
"""
import subprocess
import json
import time
import os
import sys

# Install pillow if needed
try:
    from PIL import Image
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow', '-q'])
    from PIL import Image

FRAMES_DIR = r"C:\Users\black\Desktop\agentwallet\landing-page\frames"
OUTPUT_GIF = r"C:\Users\black\Desktop\agentwallet\landing-page\demo.gif"

os.makedirs(FRAMES_DIR, exist_ok=True)

print("[OK] Frames directory ready")
print("[INFO] Taking screenshots via browser automation...")
print("[INFO] Open agentwallet.fun in browser, then run the scroll sequence")
print(f"[OUTPUT] Will save to: {OUTPUT_GIF}")
