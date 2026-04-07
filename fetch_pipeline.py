
#!/usr/bin/env python3
"""Anti-bot aware extraction pipeline for LLM-readiness analysis.

Usage:
    python llm_bulk_analyzer/fetch_pipeline.py https://example.com
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from dataclasses import dataclass
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown
from readability import Document

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class FetchResult:
    ok: bool
    method: str
    html: str
    status_code: Optional[int] = None
    error: Optional[str] = None


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def fetch_with_requests(url: str, timeout: int = 25) -> FetchResult:
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        return FetchResult(True, "requests", response.text, response.status_code)
    except Exception as exc:
        return FetchResult(False, "requests", "", error=str(exc))


def fetch_with_cloudscraper(url: str, timeout: int = 35) -> FetchResult:
    if not _has_module("cloudscraper"):
        return FetchResult(False, "cloudscraper", "", error="cloudscraper not installed")

    import cloudscraper

    try:
        scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "linux"})
        response = scraper.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        return FetchResult(True, "cloudscraper", response.text, response.status_code)
    except Exception as exc:
        return FetchResult(False, "cloudscraper", "", error=str(exc))


def fetch_with_playwright(url: str, timeout_ms: int = 45000) -> FetchResult:
    if not _has_module("playwright"):
        return FetchResult(False, "playwright", "", error="playwright not installed")

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=DEFAULT_HEADERS["User-Agent"],
                locale="en-US",
                viewport={"width": 1366, "height": 2200},
            )
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(2500)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(900)
            html = page.content()
            status_code = response.status if response else None
            browser.close()
            return FetchResult(True, "playwright", html, status_code)
    except Exception as exc:
        return FetchResult(False, "playwright", "", error=str(exc))


def clean_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for node in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        node.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_markdown(html: str) -> str:
    readable_html = Document(html).summary(html_partial=True)
    markdown = to_markdown(readable_html, heading_style="ATX")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return markdown


def get_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


def run_pipeline(url: str) -> dict:
    fetchers: list[Callable[[str], FetchResult]] = [
        fetch_with_requests,
        fetch_with_cloudscraper,
        fetch_with_playwright,
    ]

    attempts = []
    for fetcher in fetchers:
        result = fetcher(url)
        attempts.append({"method": result.method, "ok": result.ok, "error": result.error})

        if result.ok and result.html:
            html = result.html
            return {
                "status": "ok",
                "url": url,
                "method_used": result.method,
                "status_code": result.status_code,
                "title": get_title(html),
                "raw_html": html,
                "clean_text": clean_text_from_html(html),
                "markdown": extract_markdown(html),
                "attempts": attempts,
            }

    return {
        "status": "error",
        "url": url,
        "message": "All fetch methods failed. See attempts for details.",
        "attempts": attempts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch DOM + Markdown for LLM-readiness checks")
    parser.add_argument("url", help="Target URL")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(args.url)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
