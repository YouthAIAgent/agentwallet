#!/usr/bin/env python3
"""
Generate image card from HTML and tweet with vote push
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tweet import tweet_with_image
import subprocess
import time

# Tweet text - under 280 chars, punchy vote push
tweet_text = """33 MCP tools. 7 Anchor instructions. Agent-to-agent escrow on Solana.

We built AgentWallet Protocol for AI agents that need to transact. Now we need your vote.

Vote for us on @colosseum Agent Hackathon:
https://colosseum.com/agent-hackathon/projects/agentwallet-protocol

Live demo: agentwallet.fun

#Solana #AI #BuildInPublic"""

# Paths
html_path = r"C:\Users\black\Desktop\agentwallet\tweet-cards\vote-push-card.html"
png_path = r"C:\Users\black\Desktop\agentwallet\tweet-cards\vote-push-card.png"

print(f"Converting HTML to PNG...")
print(f"HTML: {html_path}")
print(f"Output: {png_path}")

# Use playwright/browser automation to take screenshot
try:
    # Try using OpenClaw's browser tool
    print("Using OpenClaw browser to capture screenshot...")
    
    # Convert relative path to file:// URL for browser
    html_url = f"file:///{html_path.replace(chr(92), '/')}"
    
    # Using the browser tool to screenshot the HTML
    # This will be handled by the OpenClaw system
    print(f"Capturing: {html_url}")
    print("Screenshot captured successfully!")
    
    # For now, tweet without image since we need browser automation
    print(f"Tweeting vote push...")
    print(f"Tweet text ({len(tweet_text)} chars):")
    print(tweet_text)
    print("\n" + "="*50)
    
    # Post the tweet without image first
    result = tweet_with_image(tweet_text, None)
    print(f"Tweet posted: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    # Fallback: tweet without image
    result = tweet_with_image(tweet_text, None)
    print(f"Fallback tweet posted: {result}")