"""Telegram Bot API channel — long messages auto-split (API limit: 4096 chars)."""
from ..net import post_clean, raise_clean
from .base import Channel

MAX_CHARS = 3800  # safety margin under Telegram's 4096-char hard limit


class TelegramChannel(Channel):
    type = "telegram"

    def send(self, subject, body):
        token = self.spec["bot_token"]
        chat_id = self.spec["chat_id"]
        api = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"*{subject}*\n\n{body}"
        for chunk in _split(text, MAX_CHARS):
            resp = post_clean(api, json={
                "chat_id": chat_id, "text": chunk, "parse_mode": "Markdown",
            }, timeout=30)
            if resp.status_code == 400:  # markdown-unfriendly chars: retry as plain text
                resp = post_clean(api, json={"chat_id": chat_id, "text": chunk}, timeout=30)
            raise_clean(resp)


def _split(text, limit):
    """Split into <=limit chunks, preferring newline boundaries."""
    chunks, rest = [], text
    while len(rest) > limit:
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:  # no usable newline nearby: hard cut
            cut = limit
        chunks.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")
    if rest:
        chunks.append(rest)
    return chunks or [""]
