"""Delivery-safety regression tests (audit #1): a failed delivery must not
mark items as seen — the next run has to retry them."""
from briefbot.engine import run_job
from briefbot.state import StateStore


def _item(n):
    return {"uid": f"s:{n}", "title": f"T{n}", "url": f"http://x/{n}",
            "text": "", "fields": {}}


class FakeSource:
    def __init__(self, items=None, exc=None):
        self.items = items if items is not None else []
        self.exc = exc
        self.id = "s"

    def collect(self):
        if self.exc:
            raise self.exc
        return self.items


class OkChannel:
    type = "ok"

    def __init__(self, spec, ctx):
        self.sent = []

    def send(self, subject, body):
        self.sent.append((subject, body))


class FailChannel:
    type = "fail"

    def __init__(self, spec, ctx):
        pass

    def send(self, subject, body):
        raise RuntimeError("delivery down")


def _patch(monkeypatch, source, channel):
    """Point the engine at fakes; returns the channel instance for inspection."""
    monkeypatch.setattr("briefbot.engine.build_source", lambda spec: source)
    if channel == "ok":
        ch = OkChannel({}, {})
        monkeypatch.setattr("briefbot.engine.build_channel", lambda spec, cfg: ch)
    else:
        ch = FailChannel({}, {})
        monkeypatch.setattr("briefbot.engine.build_channel", lambda spec, cfg: ch)
    return ch


def _job(channel_types, digest=None):
    return {
        "name": "j",
        "sources": [{"type": "rss", "id": "s"}],
        "digest": digest or {"mode": "plain"},
        "channels": [{"type": t} for t in channel_types],
    }


def test_failed_delivery_is_retried_next_run(monkeypatch):
    state = StateStore(None)
    src = FakeSource(items=[_item(1), _item(2)])
    job = _job(["fail"])

    _patch(monkeypatch, src, "fail")
    res = run_job({"jobs": [job]}, job, state)
    assert res["channels"][0]["ok"] is False
    assert not state.has_seen("j", "s:1"), "items must NOT be marked seen on failure"
    assert not state.has_seen("j", "s:2")

    ok_ch = _patch(monkeypatch, src, "ok")  # delivery recovers
    res2 = run_job({"jobs": [job]}, job, state)
    assert res2["items"] == 2, "same items must be retried and delivered"
    assert state.has_seen("j", "s:1") and state.has_seen("j", "s:2")
    assert ok_ch.sent and "T1" in ok_ch.sent[0][1]

    res3 = run_job({"jobs": [job]}, job, state)  # nothing new -> silent
    assert res3["status"] == "skipped"


def test_partial_channel_failure_still_marks_seen(monkeypatch):
    """Any one successful channel counts as delivered (no infinite re-sends)."""
    state = StateStore(None)
    src = FakeSource(items=[_item(1)])
    job = _job(["fail", "ok"])

    ok_ch, fail_ch = OkChannel({}, {}), FailChannel({}, {})

    def pick(spec, cfg):
        return ok_ch if spec["type"] == "ok" else fail_ch

    monkeypatch.setattr("briefbot.engine.build_source", lambda spec: src)
    monkeypatch.setattr("briefbot.engine.build_channel", pick)

    res = run_job({"jobs": [job]}, job, state)
    assert [c["ok"] for c in res["channels"]] == [False, True]
    assert state.has_seen("j", "s:1")


def test_watch_mode_snapshot_rollback_on_failure(monkeypatch):
    """watch_changes jobs must also retry: snapshots roll back on failure."""
    state = StateStore(None)
    src = FakeSource(items=[{"uid": "s:snap", "title": "p", "url": "",
                             "text": "", "fields": {"price": "10"}}])
    job = _job(["fail"], digest={"mode": "plain", "watch_changes": True,
                                 "only_changed": True})

    _patch(monkeypatch, src, "fail")
    run_job({"jobs": [job]}, job, state)  # fails
    assert "s" not in state.data["jobs"]["j"]["snapshots"], \
        "snapshot must be rolled back so the change is re-detected"

    _patch(monkeypatch, src, "ok")
    res2 = run_job({"jobs": [job]}, job, state)  # same change re-detected
    assert res2["changes"] >= 1
