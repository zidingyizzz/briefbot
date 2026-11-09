"""Snapshot one web page and extract watched fields via CSS selectors.

Ideal for price/stock-text watching: store last values in state, engine diffs them.
"""
from bs4 import BeautifulSoup

from ..net import http_get
from .base import Source


class PageSelectSource(Source):
    type = "page_select"

    def collect(self):
        url = self.spec["url"]
        resp = http_get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        fields = {}
        for name, selector in (self.spec.get("selectors") or {}).items():
            node = soup.select_one(selector)
            fields[name] = node.get_text(strip=True) if node else ""
        title = fields.get("title") or url
        return [{
            "uid": f"{self.id}:snapshot",
            "title": title,
            "url": url,
            "text": "; ".join(f"{k}={v}" for k, v in fields.items()),
            "fields": fields,
        }]
