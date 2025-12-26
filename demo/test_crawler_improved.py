"""Quick test of improved crawler logic."""

import asyncio
import logging
from src.tools.crawler import Crawler

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_crawler():
    print("Testing improved crawler with yun.won-giant.com")
    print("=" * 80)

    crawler = Crawler()

    # Test HTTP (should work now with minimal content)
    print("\n[Test HTTP]")
    try:
        article = crawler.crawl("http://yun.won-giant.com")
        markdown = article.to_markdown()
        print(f"Content length: {len(markdown)} chars")
        print(f"Content preview:\n{markdown[:300]}")

        if len(markdown) > 0:
            print("\nRESULT: SUCCESS - Got some content")
        else:
            print("\nRESULT: FAILED - No content")
    except Exception as e:
        print(f"\nRESULT: ERROR - {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(test_crawler())
