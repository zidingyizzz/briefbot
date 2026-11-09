"""Bark (iOS push notification) channel — https://bark.day.app

Install the Bark app on your iPhone; the device key is shown on its home page.
"""
from ..net import post_clean, raise_clean
from .base import Channel


class BarkChannel(Channel):
    type = "bark"

    def send(self, subject, body):
        key = self.spec["device_key"]
        resp = post_clean(
            "https://api.day.app/push",
            json={
                "device_key": key,
                "title": subject,
                "body": body,
                "group": self.spec.get("group", "BriefBot"),
            },
            timeout=30,
        )
        raise_clean(resp)
        # Bark reports errors inside a 200 response: {"code": 400, "message": ...}
        try:
            data = resp.json()
        except ValueError:
            return
        if isinstance(data, dict) and data.get("code") not in (200, 0, None):
            raise RuntimeError(f"bark error {data.get('code')}: {data.get('message')}")
