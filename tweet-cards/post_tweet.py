import sys
sys.path.insert(0, r'C:\Users\black\Desktop\agentwallet\scripts')
from tweet import tweet_with_image

tweet_text = """been thinking about why most AI agent wallets fail.

they wrap custodial APIs and call it "autonomous."

we built an MCP server instead. 27 tools. any agent connects, transacts natively on Solana. no keys held. no middleware.

the wallet IS the protocol.

#Solana #AIagents #Web3"""

img_path = r'C:\Users\black\Desktop\agentwallet\tweet-cards\card-pro1.png'

result = tweet_with_image(tweet_text, img_path)
print(result)
