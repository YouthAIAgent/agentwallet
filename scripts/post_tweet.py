import sys
sys.path.insert(0, r'C:\Users\black\Desktop\agentwallet\scripts')
from tweet import tweet_with_image

tweet_text = """Built AgentWallet on Anchor PDAs \u2014 every AI agent gets a deterministic vault. No private keys floating around, just program-derived addresses.

27 MCP tools. Solana-native. @armani\u2019s framework made this real.

pip install agentwallet-mcp
agentwallet.fun

#Solana #Anchor #Web3"""

img_path = r'C:\Users\black\.openclaw\media\browser\6965f171-9c50-4e07-a639-576ba3bab28a.png'

result = tweet_with_image(tweet_text, img_path)
print(result)
