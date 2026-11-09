"""Channel unit tests: Telegram splitting + 400 fallback (audit #3), Feishu
error-body detection (audit #6), Bark / ServerChan payloads (package B)."""
import pytest

from briefbot.channels.bark import BarkChannel
from briefbot.channels.feishu import FeishuChannel
from briefbot.channels.serverchan import ServerChanChannel
from briefbot.channels.telegram import TelegramChannel, _split


class FakeResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


# -- Telegram ---------------------------------------------------------------

def test_split_respects_limit_and_newlines():
    text = "\n".join(f"line {i} " + "x" * 90 for i in range(100))
    chunks = _split(text, 3800)
    assert all(len(c) <= 3800 for c in chunks)
    assert "".join(c.replace("\n", "") for c in chunks).replace(" ", "") == \
        text.replace("\n", "").replace(" ", "")


def test_split_short_text_single_chunk():
    assert _split("hello", 3800) == ["hello"]


def test_telegram_splits_long_body(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(json["text"])
        return FakeResp(200, {"ok": True})

    monkeypatch.setattr(
        "briefbot.net.requests.post", fake_post)
    ch = TelegramChannel({"bot_token": "t", "chat_id": "c"}, {})
    ch.send("S", "\n".join(f"item {i} " + "y" * 80 for i in range(120)))
    assert len(calls) > 1, "long body must be split into several messages"
    assert all(len(t) <= 3800 for t in calls)


def test_telegram_400_falls_back_to_plain(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(json)
        return FakeResp(400) if "parse_mode" in json else FakeResp(200, {"ok": True})

    monkeypatch.setattr(
        "briefbot.net.requests.post", fake_post)
    ch = TelegramChannel({"bot_token": "t", "chat_id": "c"}, {})
    ch.send("S", "body with *broken markdown")  # must not raise
    assert len(calls) == 2
    assert "parse_mode" in calls[0] and "parse_mode" not in calls[1]


# -- Feishu -----------------------------------------------------------------

def test_feishu_error_body_raises(monkeypatch):
    monkeypatch.setattr(
        "briefbot.net.requests.post",
        lambda url, json=None, timeout=None: FakeResp(200, {"code": 19021, "msg": "bad webhook"}),
    )
    ch = FeishuChannel({"webhook": "http://x"}, {})
    with pytest.raises(RuntimeError, match="19021"):
        ch.send("S", "B")


def test_feishu_success(monkeypatch):
    monkeypatch.setattr(
        "briefbot.net.requests.post",
        lambda url, json=None, timeout=None: FakeResp(200, {"code": 0, "msg": "success"}),
    )
    FeishuChannel({"webhook": "http://x"}, {}).send("S", "B")  # must not raise


# -- Bark -------------------------------------------------------------------

def test_bark_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"], captured["json"] = url, json
        return FakeResp(200, {"code": 200, "message": "ok"})

    monkeypatch.setattr(
        "briefbot.net.requests.post", fake_post)
    BarkChannel({"device_key": "KEY"}, {}).send("Subj", "Body")
    assert captured["url"] == "https://api.day.app/push"
    assert captured["json"]["device_key"] == "KEY"
    assert captured["json"]["title"] == "Subj"
    assert captured["json"]["body"] == "Body"


def test_bark_error_body_raises(monkeypatch):
    monkeypatch.setattr(
        "briefbot.net.requests.post",
        lambda url, json=None, timeout=None: FakeResp(200, {"code": 400, "message": "bad key"}),
    )
    with pytest.raises(RuntimeError, match="bad key"):
        BarkChannel({"device_key": "K"}, {}).send("S", "B")


# -- ServerChan -------------------------------------------------------------

def test_serverchan_payload(monkeypatch):
    captured = {}

    def fake_post(url, data=None, timeout=None):
        captured["url"], captured["data"] = url, data
        return FakeResp(200, {"code": 0})

    monkeypatch.setattr(
        "briefbot.net.requests.post", fake_post)
    ServerChanChannel({"send_key": "SCTKEY"}, {}).send("Subj", "Body")
    assert captured["url"] == "https://sctapi.ftqq.com/SCTKEY.send"
    assert captured["data"] == {"title": "Subj", "desp": "Body"}


def test_serverchan_error_body_raises(monkeypatch):
    monkeypatch.setattr(
        "briefbot.net.requests.post",
        lambda url, data=None, timeout=None: FakeResp(200, {"code": 400, "message": "bad key"}),
    )
    with pytest.raises(RuntimeError, match="400"):
        ServerChanChannel({"send_key": "K"}, {}).send("S", "B")
