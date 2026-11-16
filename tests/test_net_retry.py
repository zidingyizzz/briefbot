"""http_get retry tests (solidot incident, 2026-11-12).

Peak-hour feed servers hang connections until the read timeout fires;
http_get must retry transient failures (timeouts, 429/5xx) and give up
immediately on deliberate refusals (other 4xx). backoff=0 keeps tests fast.
"""
import requests

from briefbot.net import HttpError, http_get, raise_clean


class _Resp:
    def __init__(self, code, reason="Forbidden"):
        self.status_code = code
        self.reason = reason

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def _install(monkeypatch, outcomes):
    """Serve the queued outcomes per call; record how many calls were made."""
    calls = {"n": 0}

    def fake_get(url, timeout=None, headers=None):
        calls["n"] += 1
        outcome = outcomes[min(calls["n"] - 1, len(outcomes) - 1)]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def test_timeout_then_success_retries(monkeypatch):
    calls = _install(monkeypatch, [requests.exceptions.ReadTimeout("t"), _Resp(200)])
    resp = http_get("https://example/feed", attempts=3, backoff=0)
    assert resp.status_code == 200
    assert calls["n"] == 2, "first attempt timed out, second must be tried"


def test_503_then_success_retries(monkeypatch):
    calls = _install(monkeypatch, [_Resp(503, "Service Unavailable"), _Resp(200)])
    resp = http_get("https://example/feed", attempts=3, backoff=0)
    assert resp.status_code == 200
    assert calls["n"] == 2


def test_4xx_not_retried(monkeypatch):
    calls = _install(monkeypatch, [_Resp(403)])
    try:
        http_get("https://example/feed", attempts=3, backoff=0)
        raise AssertionError("403 must raise HttpError")
    except HttpError as exc:
        assert exc.status_code == 403
    assert calls["n"] == 1, "a deliberate refusal must not be retried"


def test_persistent_timeout_reports_attempts(monkeypatch):
    _install(monkeypatch, [requests.exceptions.ConnectionError("reset")])
    try:
        http_get("https://example/feed", attempts=2, backoff=0)
        raise AssertionError("persistent failure must raise")
    except RuntimeError as exc:
        msg = str(exc)
        assert "failed after 2 attempts" in msg
        assert "network error (ConnectionError)" in msg
        assert "https://example/feed" not in msg, "errors stay URL-free"


def test_backoff_sleeps_between_attempts(monkeypatch):
    import briefbot.net as net
    _install(monkeypatch, [requests.exceptions.ReadTimeout("t")])
    sleeps = []
    monkeypatch.setattr(net.time, "sleep", lambda s: sleeps.append(s))
    try:
        http_get("https://example/feed", attempts=3, backoff=5)
        raise AssertionError("persistent failure must raise")
    except RuntimeError as exc:
        assert "failed after 3 attempts" in str(exc)
    assert sleeps == [5, 10], "linear backoff between the three attempts"


def test_raise_clean_url_free_message():
    try:
        raise_clean(_Resp(403, "Forbidden"))
        raise AssertionError("403 must raise")
    except HttpError as exc:
        assert str(exc) == "HTTP 403 Forbidden"
        assert isinstance(exc, RuntimeError), "callers catch RuntimeError today"
