"""Job orchestration: collect -> diff/state -> digest -> push."""
import datetime
import logging

from .channels import build_channel
from .digest import plain_digest
from .digest.llm import llm_digest
from .sources import build_source

log = logging.getLogger("briefbot.engine")

DEFAULT_MAX_ITEMS = 30
DEFAULT_ALERT_AFTER_FAILURES = 3


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _fmt(template, ctx):
    try:
        return template.format_map(_SafeDict(ctx))
    except Exception:
        return template


def _fields_short(fields):
    return ", ".join(f"{k}={v}" for k, v in fields.items()) if fields else ""


def _source_label(spec):
    return spec.get("id") or spec.get("url") or spec.get("type", "?")


def _source_warnings(state, name, threshold):
    """Human-readable lines for sources that keep failing."""
    lines = []
    for sid, fails, last_ok in state.failing_sources(name, threshold):
        when = (
            datetime.date.fromtimestamp(last_ok).isoformat() if last_ok else "never"
        )
        lines.append(
            f"⚠️ Source '{sid}' failed {fails} runs in a row "
            f"(last ok: {when}) — today's brief may be incomplete."
        )
    return lines


def run_job(cfg, job, state, dry_run=False):
    """Run one job end-to-end. Returns a result dict for CLI reporting."""
    name = job["name"]
    digest_cfg = job.get("digest") or {}
    only_new = digest_cfg.get("only_new", True)
    watch_changes = digest_cfg.get("watch_changes", False)
    only_changed = digest_cfg.get("only_changed", False)
    mode = digest_cfg.get("mode", "llm")
    max_items = int(digest_cfg.get("max_items", DEFAULT_MAX_ITEMS))
    alert_after = int(
        digest_cfg.get("alert_after_failures", DEFAULT_ALERT_AFTER_FAILURES)
    )

    items, changes, errors = [], [], []
    checkpoint = state.checkpoint(name)  # seen/snapshots as they were

    # 1) collect from every source
    for spec in job.get("sources", []):
        sid = _source_label(spec)
        try:
            src = build_source(spec)
            fresh = src.collect()
        except Exception as exc:
            errors.append(f"{sid}: {exc}")
            state.report_source(name, sid, ok=False)
            log.warning("source failed in job %s: %s", name, errors[-1])
            continue
        state.report_source(name, sid, ok=True)

        if watch_changes:
            for it in fresh:
                old_fields = state.snapshot(name, src.id, it["fields"])
                if old_fields is None:
                    changes.append({
                        "source": src.id, "field": "(first snapshot)",
                        "old": "", "new": _fields_short(it["fields"]) or "(empty)",
                    })
                else:
                    for field, new_val in it["fields"].items():
                        old_val = old_fields.get(field, "")
                        if str(new_val) != str(old_val):
                            changes.append({
                                "source": src.id, "field": field,
                                "old": str(old_val), "new": str(new_val),
                            })
                items.append(it)
        else:
            for it in fresh:
                if only_new and state.has_seen(name, it["uid"]):
                    continue
                items.append(it)
                # NOTE: mark_seen is deferred until delivery succeeds.

    warnings = _source_warnings(state, name, alert_after)

    # Early exits — unless a source-health warning needs raising, silence
    # is the product's default behavior.
    nothing_to_say = (
        (errors and not items and not changes)
        or (only_changed and not changes)
        or (only_new and not watch_changes and not items)
    )
    if nothing_to_say and not warnings:
        state.save()
        if errors and not items and not changes:
            return {"job": name, "status": "error", "errors": errors}
        if only_changed and not changes:
            return {"job": name, "status": "skipped", "reason": "no field changes"}
        return {"job": name, "status": "skipped", "reason": "no new items"}

    # 2) digest (LLM if configured and key present, plain otherwise)
    if nothing_to_say and warnings:
        body = "\n".join(warnings)  # health alert only, nothing else to report
    else:
        body = None
        if mode == "llm":
            try:
                body = llm_digest(cfg, items, digest_cfg.get("system_prompt"), name)
            except Exception as exc:
                log.warning("LLM digest failed, falling back to plain list: %s", exc)
        if body is None:
            body = plain_digest(
                items, changes if watch_changes else None, max_items=max_items
            )
        if warnings:
            body = "\n".join(warnings) + "\n\n" + body

    # 3) render subject and push
    today = datetime.date.today().isoformat()
    ctx = {"job_name": name, "today": today,
           "items": len(items), "changes": len(changes)}
    subject = _fmt(job.get("subject") or "BriefBot: {job_name} — {today}", ctx)
    if nothing_to_say and warnings:
        subject += " ⚠️"

    channel_specs = [{"type": "stdout"}] if dry_run else job.get("channels", [])
    statuses = []
    for spec in channel_specs:
        try:
            channel = build_channel(spec, cfg)
            channel.send(subject, body)
            statuses.append({"channel": spec.get("type"), "ok": True})
        except Exception as exc:
            log.error("channel %s failed: %s", spec.get("type"), exc)
            statuses.append({"channel": spec.get("type"), "ok": False, "error": str(exc)})

    delivered = any(ch.get("ok") for ch in statuses)
    if not delivered and (items or changes):
        # Every channel failed: roll back so the next run retries everything.
        state.restore(name, checkpoint)
        log.error(
            "job %s: all channels failed — state rolled back, "
            "items/changes will be retried next run", name,
        )
    elif not watch_changes:
        for it in items:
            state.mark_seen(name, it["uid"])

    state.save()
    # A warnings-only push still means "sources failing — needs attention",
    # so the run keeps error semantics (exit code 1) for monitors.
    status = "error" if (nothing_to_say and warnings) else "ok"
    return {"job": name, "status": status,
            "items": 0 if nothing_to_say else len(items),
            "changes": 0 if nothing_to_say else len(changes),
            "channels": statuses, "errors": errors}
