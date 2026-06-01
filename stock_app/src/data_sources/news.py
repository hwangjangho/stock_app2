from __future__ import annotations

from typing import List, Dict
from urllib.parse import quote

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def google_news_search(query: str, max_results: int = 10) -> List[Dict]:
    q = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"

    feed = feedparser.parse(rss_url)

    items = []
    for entry in feed.entries[:max_results]:
        title = getattr(entry, "title", "").strip()
        url = getattr(entry, "link", "").strip()
        published = getattr(entry, "published", "")

        item = {
            "title": title,
            "url": url,
            "source": "Google News",
            "text": title,
            "published_at": published,
        }

        item = _enrich_article(item)
        items.append(item)

    return items


def _enrich_article(item: Dict) -> Dict:
    url = item.get("url", "")
    if not url:
        return item

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        paragraphs = []
        for p in soup.find_all("p"):
            txt = p.get_text(" ", strip=True)
            if txt and len(txt) > 30:
                paragraphs.append(txt)

        if paragraphs:
            item["text"] = " ".join(paragraphs)[:3000]
    except Exception:
        pass

    if not item.get("text"):
        item["text"] = item.get("title", "")

    return item