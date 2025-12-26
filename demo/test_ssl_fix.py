"""Test SSL certificate error fix."""

import logging
from src.tools.crawler.jina_client import JinaClient

logging.basicConfig(level=logging.INFO)

print("Testing SSL certificate error fix...")
print("=" * 80)

client = JinaClient()

test_url = "https://yun.won-giant.com"
print(f"\n[Test] Crawling URL: {test_url}")
print("-" * 80)

result = client.crawl(test_url)

print("\n[Result]")
print("-" * 80)
if result.startswith("Error:"):
    print("FAILED: Still got error")
    print(result[:200])
else:
    print("SUCCESS: Got content")
    print(f"Content length: {len(result)} chars")
    print(f"Content preview: {result[:200]}...")

print("\n" + "=" * 80)
