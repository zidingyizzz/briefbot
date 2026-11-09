"""Source-health alert tests (audit #5): failing sources surface in the brief."""
from briefbot.engine import run_job
from briefbot.state import StateStore

from test_delivery_safety import FakeSource, OkChannel, _item


def _job(alert_after=2):
    return {
        "name": "j",
        "sources": [{"type": "rss", "id": "good"}, {"type": "rss", "id": "bad"}],
        "digest": {"mode": "plain", "alert_after_failures": alert_after},
        "channels": [{"type": "ok"}],
    }


def _setup(monkeypatch, good, bad):
    def pick_source(spec):
        return bad if spec["id"] == "bad" else good

    ok_ch = OkChannel({}, {})
    monkeypatch.setattr("briefbot.engine.build_source", pick_source)
    monkeypatch.setattr("briefbot.engine.build_channel", lambda spec, cfg: ok_ch)
    return ok_ch


def test_consecutive_failures_raise_warning(monkeypatch):
    state = StateStore(None)
    job = _job(alert_after=2)
    good = FakeSource(items=[])
    bad = FakeSource(exc=RuntimeError("feed gone"))
    ok_ch = _setup(monkeypatch, good, bad)

    res1 = run_job({"jobs": [job]}, job, state)   # fails=1: silent, no alert yet
    assert res1["status"] == "error"
    assert not ok_ch.sent

    res2 = run_job({"jobs": [job]}, job, state)   # fails=2: warning-only brief
    assert res2["status"] == "error", \
        "warnings-only runs keep error semantics (exit code) for monitors"
    assert ok_ch.sent, "a health warning must be pushed even with no new items"
    body = ok_ch.sent[-1][1]
    assert "bad" in body and "2 runs in a row" in body


def test_recovery_resets_counter(monkeypatch):
    state = StateStore(None)
    job = _job(alert_after=2)
    good = FakeSource(items=[])
    bad = FakeSource(exc=RuntimeError("feed gone"))
    ok_ch = _setup(monkeypatch, good, bad)

    run_job({"jobs": [job]}, job, state)
    run_job({"jobs": [job]}, job, state)
    assert state.failing_sources("j", 2)

    bad.exc = None  # source recovers
    bad.items = [_item(9)]
    res = run_job({"jobs": [job]}, job, state)
    assert res["items"] == 1
    assert not state.failing_sources("j", 2)
    assert "runs in a row" not in ok_ch.sent[-1][1], \
        "a recovered source must not keep warning"


def test_warning_prepended_to_normal_brief(monkeypatch):
    state = StateStore(None)
    job = _job(alert_after=1)
    good = FakeSource(items=[_item(1)])
    bad = FakeSource(exc=RuntimeError("down"))
    ok_ch = _setup(monkeypatch, good, bad)

    res = run_job({"jobs": [job]}, job, state)
    assert res["items"] == 1
    body = ok_ch.sent[0][1]
    assert body.startswith("⚠️ Source 'bad'")
    assert "T1" in body, "the actual items must still be delivered"
