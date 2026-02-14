# -*- coding: utf-8 -*-
"""Post PDA Wallet Thread as a proper Twitter thread (10 tweets chained)"""
import sys, os, io, json, time

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"C:\Users\black\Desktop\agentwallet\scripts")
from tweet import get_client

CARD_DIR = r"C:\Users\black\Desktop\agentwallet\pda-wallet-thread"

# Thread tweets — each with card
TWEETS = [
    {
        "text": "your AI agent is moving real money on-chain right now.\n\nno spending limits. no revocation. no audit trail.\n\njust a raw private key sitting in an env variable.\n\nhere's why PDA wallets change everything -- and how we built one. [1/10]",
        "card": "card_01.png"
    },
    {
        "text": "every AI wallet today works the same way:\n\ngenerate keypair -> store private key -> agent signs everything\n\none leaked .env file. one compromised server. one rogue LLM hallucination.\n\nyour funds are gone. all of them. instantly.\n\nthere is no \"undo\" on-chain. [2/10]",
        "card": "card_02.png"
    },
    {
        "text": "PDA wallets flip the model:\n\ninstead of giving your agent a key, you give it PERMISSIONS.\n\nthe wallet has no private key. the program controls it. the agent operates within boundaries you set.\n\nhouse keys vs room key with a time lock. [3/10]",
        "card": "card_03.png"
    },
    {
        "text": "this is what on-chain spend policies look like:\n\nAgentPolicy -- max_per_tx, daily_limit, allowed_tokens, destinations, cooldown, emergency_freeze\n\nenforced by Solana's runtime. not by your agent. not by a server. by the VM itself. [4/10]",
        "card": "card_04.png"
    },
    {
        "text": "the real unlock: multi-agent isolation.\n\nagent A: trading bot -- 10 SOL/day, Jupiter only\nagent B: NFT bidder -- 2 SOL/tx, Tensor only\nagent C: treasury -- read-only, reports only\n\neach agent gets its own PDA. its own permissions.\n\none compromised agent can't touch the others. [5/10]",
        "card": "card_05.png"
    },
    {
        "text": "the numbers that matter:\n\n400ms confirmation\n$0.00025 per transaction\n12ms API response\n30x faster than Ethereum\n\nyour agent doesn't wait 12 seconds to confirm. it doesn't pay $5 in gas.\n\nit moves at the speed of thought. on @solana. [6/10]",
        "card": "card_06.png"
    },
    {
        "text": "hot take: if you can't revoke your AI agent's access in under 1 second, you don't have security. you have hope.\n\nPDA wallets: one instruction. instant freeze.\n\nprivate key wallets: move all funds to a new wallet. pray the agent doesn't drain first. [7/10]",
        "card": "card_07.png"
    },
    {
        "text": "one atomic transaction. zero private keys:\n\ninvoke_signed -- jupiter swap, raydium liquidity, marinade stake -- all in one tx.\n\nif any step fails, everything reverts. no partial states. no stuck funds.\n\nCPI composability. Solana-native. [8/10]",
        "card": "card_08.png"
    },
    {
        "text": "what we shipped with @agentwallet_pro:\n\n33 MCP tools. PDA-native wallets. on-chain spend policies. real-time audit logs.\n\nplug into any AI via Model Context Protocol.\n\nnot a pitch deck. not a prototype. shipped code. [9/10]",
        "card": "card_09.png"
    },
    {
        "text": "the future of AI agents is on-chain. but only if we build the guardrails first.\n\nPDA wallets are those guardrails.\n\nagentwallet.fun\n@agentwallet_pro\n\nRT tweet 1 if this helped. let's build the agent economy on @solana. [10/10]",
        "card": "card_10.png"
    },
]

def post_thread():
    client, api_v1 = get_client()
    
    prev_id = None
    urls = []
    
    for i, tweet in enumerate(TWEETS):
        card_path = os.path.join(CARD_DIR, tweet["card"])
        
        # Upload image
        print(f"[UPLOAD] {tweet['card']}")
        media = api_v1.media_upload(filename=card_path)
        media_id = media.media_id
        
        # Build tweet params
        kwargs = {
            "text": tweet["text"],
            "media_ids": [media_id]
        }
        
        # Chain as reply to previous tweet
        if prev_id:
            kwargs["in_reply_to_tweet_id"] = prev_id
        
        print(f"[POST {i+1}/10]...")
        response = client.create_tweet(**kwargs)
        tweet_id = response.data["id"]
        url = f"https://x.com/Web3__Youth/status/{tweet_id}"
        
        print(f"[OK {i+1}/10] {url}")
        urls.append(url)
        prev_id = tweet_id
        
        # Rate limit safety
        if i < len(TWEETS) - 1:
            time.sleep(3)
    
    print(f"\nDONE! Thread start: {urls[0]}")
    return urls

if __name__ == "__main__":
    post_thread()
