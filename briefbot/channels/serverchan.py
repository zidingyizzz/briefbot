"""Server酱 (ServerChan Turbo) channel — WeChat push via https://sct.ftqq.com

Send key comes from the Server酱 site after scanning the QR code with WeChat;
messages land in the "Server酱" WeChat service app.
"""
from ..net import post_clean, raise_clean
from .base import Channel


class ServerChanChannel(Channel):
    type = "serverchan"

    def send(self, subject, body):
        key = self.spec["send_key"]
        resp = post_clean(
            f"https://sctapi.ftqq.com/{key}.send",
            data={"title": subject, "desp": body},
            timeout=30,
        )
        raise_clean(resp)
        # Server酱 reports errors inside a 200 response: {"code": 400, ...}
        try:
            data = resp.json()
        except ValueError:
            return
        if isinstance(data, dict) and data.get("code") not in (0, None):
            raise RuntimeError(f"serverchan error {data.get('code')}: {data.get('message')}")
