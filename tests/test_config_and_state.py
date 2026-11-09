"""Config interpolation + validation, and StateStore behavior."""
import pytest

from briefbot.config import load_config
from briefbot.state import StateStore


def _write(tmp_path, text):
    p = tmp_path / "cfg.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


CFG = """
jobs:
  - name: j
    sources:
      - type: rss
        url: ${FEED_URL}
    digest: {mode: plain}
    channels:
      - type: stdout
        token: ${TOKEN:-fallback}
"""


def test_env_var_interpolation(tmp_path, monkeypatch):
    monkeypatch.setenv("FEED_URL", "https://example.com/feed")
    monkeypatch.setenv("TOKEN", "real")
    cfg = load_config(_write(tmp_path, CFG))
    job = cfg["jobs"][0]
    assert job["sources"][0]["url"] == "https://example.com/feed"
    assert job["channels"][0]["token"] == "real"


def test_default_when_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("FEED_URL", raising=False)
    monkeypatch.delenv("TOKEN", raising=False)
    cfg = load_config(_write(tmp_path, CFG))
    job = cfg["jobs"][0]
    assert job["sources"][0]["url"] == ""
    assert job["channels"][0]["token"] == "fallback"


def test_validation_requires_jobs_and_channels(tmp_path):
    with pytest.raises(ValueError, match="jobs"):
        load_config(_write(tmp_path, "llm: {api_key: x}\n"))
    with pytest.raises(ValueError, match="channels"):
        load_config(_write(tmp_path, """
jobs:
  - name: j
    sources: [{type: rss, url: http://x}]
"""))


# -- StateStore -------------------------------------------------------------

def test_seen_dedupe_and_cap():
    st = StateStore(None)
    assert not st.has_seen("j", "a")
    st.mark_seen("j", "a")
    assert st.has_seen("j", "a")
    st.mark_seen("j", "a")  # idempotent
    assert st.data["jobs"]["j"]["seen"] == ["a"]

    for i in range(10):
        st.mark_seen("j", f"u{i}", cap=5)
    seen = st.data["jobs"]["j"]["seen"]
    assert len(seen) == 5 and seen[-1] == "u9"


def test_checkpoint_restore_preserves_health():
    st = StateStore(None)
    st.mark_seen("j", "old")
    st.snapshot("j", "src", {"price": "1"})
    cp = st.checkpoint("j")

    st.mark_seen("j", "new")            # would-be-persisted changes...
    st.snapshot("j", "src", {"price": "2"})
    st.report_source("j", "src", ok=False)
    st.report_source("j", "src", ok=False)

    st.restore("j", cp)                 # ...rolled back
    assert st.data["jobs"]["j"]["seen"] == ["old"]
    assert st.data["jobs"]["j"]["snapshots"]["src"]["fields"] == {"price": "1"}
    # health survives the rollback (it must persist even on failed delivery)
    assert st.failing_sources("j", 2) == [("src", 2, None)]


def test_transient_never_writes_back():
    st = StateStore(None)
    st.mark_seen("j", "a")
    clone = st.transient()
    clone.mark_seen("j", "b")
    assert not st.has_seen("j", "b")
