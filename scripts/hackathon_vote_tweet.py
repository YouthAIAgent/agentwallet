#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tweet import tweet_with_image

# Tweet text - under 280 chars, punchy vote push
tweet_text = """33 MCP tools. 7 Anchor instructions. Agent-to-agent escrow on Solana.

We built AgentWallet Protocol for AI agents that need to transact. Now we need your vote.

Vote for us on @colosseum Agent Hackathon:
https://colosseum.com/agent-hackathon/projects/agentwallet-protocol

Live demo: agentwallet.fun

#Solana #AI #BuildInPublic"""

# Image path
image_path = r"C:\Users\black\Desktop\agentwallet\tweet-cards\vote-push-card.html"

print(f"Tweeting with image: {image_path}")
print(f"Tweet text ({len(tweet_text)} chars):")
print(tweet_text)
print("\n" + "="*50)

# Post the tweet
result = tweet_with_image(tweet_text, image_path)
print(f"Tweet result: {result}")