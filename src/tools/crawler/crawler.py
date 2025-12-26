import re
import logging

from src.config import CrawlerEngine, load_yaml_config
from src.tools.crawler.article import Article
from src.tools.crawler.infoquest_client import InfoQuestClient
from src.tools.crawler.jina_client import JinaClient
from src.tools.crawler.readability_extractor import ReadabilityExtractor

logger = logging.getLogger(__name__)


def safe_truncate(text: str, max_length: int = 500) -> str:
    """
    Safely truncate text to a maximum length without breaking multi-byte characters.

    Args:
        text: The text to truncate
        max_length: Maximum number of characters to keep

    Returns:
        Truncated text that is safe to use without encoding issues
    """
    if text is None:
        return None

    if len(text) <= max_length:
        return text

    if max_length < 3:
        return "..."[:max_length]

    try:
        import textwrap
        return textwrap.shorten(text, width=max_length, placeholder="...")
    except (ImportError, TypeError):
        truncated = text[:max_length - 3]
        while truncated and ord(truncated[-1]) >= 0xD800 and ord(truncated[-1]) <= 0xDFFF:
            truncated = truncated[:-1]
        return truncated + "..."


def is_html_content(content: str) -> bool:
    """
    Check if the provided content is HTML.

    Uses a more robust detection method that checks for common HTML patterns
    including DOCTYPE declarations, HTML tags, and other HTML markers.
    """
    if not content or not content.strip():
        return False

    content = content.strip()

    if content.startswith('<!--') and '-->' in content:
        return True

    if re.match(r'^<!DOCTYPE\s+html', content, re.IGNORECASE):
        return True

    if content.startswith('<?xml') and '<html' in content:
        return True

    html_start_patterns = [
        r'^<html',
        r'^<head',
        r'^<body',
        r'^<title',
        r'^<meta',
        r'^<link',
        r'^<script',
        r'^<style',
        r'^<div',
        r'^<p>',
        r'^<p\s',
        r'^<span',
        r'^<h[1-6]',
        r'^<!DOCTYPE',
        r'^<\!DOCTYPE',
    ]

    for pattern in html_start_patterns:
        if re.match(pattern, content, re.IGNORECASE):
            return True

    if re.search(r'<[^>]+>', content):
        html_indicators = [
            r'href\s*=',
            r'src\s*=',
            r'class\s*=',
            r'id\s*=',
            r'<img\s',
            r'<a\s',
            r'<div',
            r'<p>',
            r'<p\s',
            r'<!DOCTYPE',
        ]

        for indicator in html_indicators:
            if re.search(indicator, content, re.IGNORECASE):
                return True

        self_closing_tags = [
            r'<img\s+[^>]*?/>',
            r'<br\s*/?>',
            r'<hr\s*/?>',
            r'<input\s+[^>]*?/>',
            r'<meta\s+[^>]*?/>',
            r'<link\s+[^>]*?/>',
        ]

        for tag in self_closing_tags:
            if re.search(tag, content, re.IGNORECASE):
                return True

    return False


class Crawler:
    def crawl(self, url: str) -> Article:
        config = load_yaml_config("conf.yaml")
        crawler_config = config.get("CRAWLER_ENGINE", {})

        crawler_client = self._select_crawler_tool(crawler_config)
        html = self._crawl_with_tool(crawler_client, url)

        if not html or not html.strip():
            logger.warning(f"Empty content received from URL {url}")
            article = Article(
                title="Empty Content",
                html_content="<p>No content could be extracted from this page</p>"
            )
            article.url = url
            return article

        if not is_html_content(html):
            logger.warning(f"Non-HTML content received from URL {url}, creating fallback article")
            article = Article(
                title="Non-HTML Content",
                html_content=f"<p>This URL returned content that cannot be parsed as HTML. Raw content: {safe_truncate(html, 500)}</p>"
            )
            article.url = url
            return article

        try:
            extractor = ReadabilityExtractor()
            article = extractor.extract_article(html)
        except Exception as e:
            logger.error(f"Failed to extract article from {url}: {repr(e)}")
            article = Article(
                title="Content Extraction Failed",
                html_content=f"<p>Content extraction failed. Raw content: {safe_truncate(html, 500)}</p>"
            )
            article.url = url
            return article

        article.url = url
        return article

    def _select_crawler_tool(self, crawler_config: dict):
        engine = crawler_config.get("engine", CrawlerEngine.JINA.value)

        if engine == CrawlerEngine.JINA.value:
            logger.info(f"Selecting Jina crawler engine")
            return JinaClient()
        elif engine == CrawlerEngine.INFOQUEST.value:
            logger.info(f"Selecting InfoQuest crawler engine")
            fetch_time = crawler_config.get("fetch_time", -1)
            timeout = crawler_config.get("timeout", -1)
            navi_timeout = crawler_config.get("navi_timeout", -1)

            if fetch_time > 0 or timeout > 0 or navi_timeout > 0:
                logger.debug(
                    f"Initializing InfoQuestCrawler with parameters: "
                    f"fetch_time={fetch_time}, "
                    f"timeout={timeout}, "
                    f"navi_timeout={navi_timeout}"
                )

            return InfoQuestClient(
                fetch_time=fetch_time,
                timeout=timeout,
                navi_timeout=navi_timeout
            )
        else:
            raise ValueError(f"Unsupported crawler engine: {engine}")

    def _crawl_with_tool(self, crawler_client, url: str) -> str:
        logger.info(f"Crawling URL: {url} using {crawler_client.__class__.__name__}")
        try:
            return crawler_client.crawl(url, return_format="html")
        except Exception as e:
            logger.error(f"Failed to fetch URL {url} using {crawler_client.__class__.__name__}: {repr(e)}")
            raise
