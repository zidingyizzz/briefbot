"""Plain (no-LLM) digest renderer."""


def plain_digest(items, changes=None, max_items=30):
    lines = []
    if changes:
        lines.append("Changes")
        for c in changes:
            old = c["old"] if c["old"] else "(none)"
            lines.append(f"- [{c['source']}] {c['field']}: {old} -> {c['new']}")
        lines.append("")
    if items:
        lines.append("Items")
        for it in items[:max_items]:
            url = f" ({it['url']})" if it.get("url") else ""
            lines.append(f"- {it.get('title', '(untitled)')}{url}")
        if len(items) > max_items:
            more = len(items) - max_items
            lines.append("")
            lines.append(
                f"(+{more} more not shown — raise `digest.max_items` to include them)"
            )
    return "\n".join(lines) if lines else "(nothing to report)"
