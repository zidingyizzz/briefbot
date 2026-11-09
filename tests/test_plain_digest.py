"""Plain digest rendering: truncation must be visible, not silent (audit #2)."""
from briefbot.digest import plain_digest


def _items(n):
    return [{"uid": f"s:{i}", "title": f"Item {i}", "url": f"http://x/{i}",
             "text": "", "fields": {}} for i in range(n)]


def test_no_truncation_note_when_under_cap():
    body = plain_digest(_items(5))
    assert body.count("- ") == 5
    assert "more" not in body


def test_truncation_shows_more_note():
    body = plain_digest(_items(40))
    item_lines = [ln for ln in body.splitlines() if ln.startswith("- ")]
    assert len(item_lines) == 30
    assert "(+10 more not shown" in body
    assert "digest.max_items" in body


def test_max_items_override():
    body = plain_digest(_items(10), max_items=5)
    assert "(+5 more not shown" in body


def test_changes_rendered_before_items():
    body = plain_digest(
        _items(1),
        changes=[{"source": "s", "field": "price", "old": "10", "new": "12"}],
    )
    assert body.splitlines()[0] == "Changes"
    assert "price: 10 -> 12" in body
    assert "Item 0" in body
