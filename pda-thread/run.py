"""Runner: generate all 15 cards using Playwright"""
import asyncio, shutil, sys
from pathlib import Path

# Add current dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright
from cards_01_05 import card_01, card_02, card_03, card_04, card_05
from cards_06_10 import card_06, card_07, card_08, card_09, card_10
from cards_11_15 import card_11, card_12, card_13, card_14, card_15

OUT = Path(r"C:\Users\black\Desktop\agentwallet\pda-thread")
MEDIA = Path(r"C:\Users\black\.openclaw\media")

CARDS = {
    1: card_01, 2: card_02, 3: card_03, 4: card_04, 5: card_05,
    6: card_06, 7: card_07, 8: card_08, 9: card_09, 10: card_10,
    11: card_11, 12: card_12, 13: card_13, 14: card_14, 15: card_15,
}

async def main():
    MEDIA.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})

        for num, fn in CARDS.items():
            html_content = fn()
            fname = f"card_{num:02d}.png"
            out_path = OUT / fname
            media_path = MEDIA / fname

            await page.set_content(html_content, wait_until="networkidle")
            # Wait for fonts to load
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(out_path), type="png")
            
            # Copy to media dir
            shutil.copy2(str(out_path), str(media_path))
            print(f"[OK] {fname}")

        await browser.close()
    print("\nAll 15 cards generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
