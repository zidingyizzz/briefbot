"""Source registry — `type:` in job config maps to a class here."""
from .page_select import PageSelectSource
from .rss import RssSource
from .static_json import StaticJsonSource

SOURCES = {
    cls.type: cls
    for cls in (RssSource, PageSelectSource, StaticJsonSource)
}


def build_source(spec):
    stype = spec.get("type")
    if stype not in SOURCES:
        raise ValueError(
            f"unknown source type {stype!r} (available: {', '.join(sorted(SOURCES))})"
        )
    return SOURCES[stype](spec)
