"""JSON-backed state: seen item ids + last field snapshots, per job."""
import json
import os
import time


class StateStore:
    def __init__(self, path):
        self.path = path
        self.data = {"jobs": {}}
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                self.data = json.load(fh)

    def _job(self, name):
        return self.data["jobs"].setdefault(name, {"seen": [], "snapshots": {}})

    def has_seen(self, job, uid):
        return uid in self._job(job).get("seen", [])

    def mark_seen(self, job, uid, cap=500):
        seen = self._job(job).setdefault("seen", [])
        if uid not in seen:
            seen.append(uid)
        del seen[:-cap]  # keep the newest `cap` ids only

    def snapshot(self, job, source_id, fields):
        """Store the latest fields; return the previous fields (None on first run)."""
        snaps = self._job(job).setdefault("snapshots", {})
        old = snaps.get(source_id)
        snaps[source_id] = {"fields": fields, "ts": time.time()}
        return old.get("fields") if old else None

    # -- source health tracking (consecutive failures per source) --

    def report_source(self, job, source_id, ok):
        """Record per-source health: consecutive failure count + last success."""
        health = self._job(job).setdefault("health", {})
        rec = health.setdefault(source_id, {"fails": 0, "last_ok": None})
        if ok:
            rec["fails"] = 0
            rec["last_ok"] = time.time()
        else:
            rec["fails"] = int(rec.get("fails") or 0) + 1

    def failing_sources(self, job, threshold=3):
        """[(source_id, consecutive_failures, last_ok_ts)] for sources past threshold."""
        out = []
        for sid, rec in (self._job(job).get("health") or {}).items():
            fails = int(rec.get("fails") or 0)
            if fails >= threshold:
                out.append((sid, fails, rec.get("last_ok")))
        return out

    # -- delivery-safety rollback --

    def checkpoint(self, job):
        """Copy the job's seen/snapshots so a failed delivery can be rolled back."""
        data = self._job(job)
        return {
            "seen": list(data.get("seen") or []),
            "snapshots": json.loads(json.dumps(data.get("snapshots") or {})),
        }

    def restore(self, job, checkpoint):
        """Undo in-memory seen/snapshots changes since checkpoint() (keeps health)."""
        data = self._job(job)
        data["seen"] = checkpoint["seen"]
        data["snapshots"] = checkpoint["snapshots"]

    def save(self):
        if not self.path:
            return
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=2)

    def transient(self):
        """Return an in-memory copy for dry runs: reads current state, never saves."""
        clone = StateStore(None)
        clone.data = json.loads(json.dumps(self.data))
        return clone
