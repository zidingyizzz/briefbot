"""RSS / Atom feed source (URLs via shared HTTP client, or local file paths)."""
import feedparser

from ..net import http_get
from .base import Source


class RssSource(Source):
    type = "rss"

    def collect(self):
        target = self.spec["url"]
        if target.startswith("http://") or target.startswith("https://"):
            resp = http_get(target)
            parsed = feedparser.parse(resp.content)
        else:
            with open(target, "r", encoding="utf-8") as fh:
                parsed = feedparser.parse(fh.read())
        if parsed.bozo and not parsed.entries:
            # No URL in the message — the engine already prefixes the source id.
            raise RuntimeError(f"failed to parse feed: {parsed.bozo_exception}")
        limit = int(self.spec.get("limit", 30))
        items = []
        for entry in parsed.entries[:limit]:
            uid = entry.get("id") or entry.get("link") or entry.get("title")
            if not uid:
                continue
            title = entry.get("title", "(untitled)")
            summary = entry.get("summary", "")
            items.append({
                "uid": f"{self.id}:{uid}",
                "title": title,
                "url": entry.get("link", ""),
                "text": f"{title}. {summary}"[:1500],
                "fields": {},
            })
        return items
