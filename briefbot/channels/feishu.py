"""Feishu (Lark) custom-bot webhook channel."""
from ..net import post_clean, raise_clean
from .base import Channel


class FeishuChannel(Channel):
    type = "feishu"

    def send(self, subject, body):
        webhook = self.spec["webhook"]
        payload = {"msg_type": "text", "content": {"text": f"{subject}\n\n{body}"}}
        resp = post_clean(webhook, json=payload, timeout=30)
        raise_clean(resp)
        # Feishu reports most errors inside a 200 response: {"code": 19021, ...}
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError("feishu: unexpected non-JSON response")
        if isinstance(data, dict) and data.get("code") not in (0, None):
            raise RuntimeError(f"feishu error {data.get('code')}: {data.get('msg')}")
