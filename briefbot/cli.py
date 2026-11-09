"""BriefBot command line."""
import argparse
import logging
import sys
import time

from .config import load_config
from .engine import run_job
from .state import StateStore


def _render(result):
    parts = [f"[{result['job']}] {result['status']}"]
    if "items" in result:
        parts.append(f"items={result['items']}")
    if "changes" in result:
        parts.append(f"changes={result['changes']}")
    if result.get("reason"):
        parts.append(f"reason={result['reason']}")
    for err in result.get("errors", []):
        parts.append(f"error={err}")
    for ch in result.get("channels", []):
        tag = "ok" if ch.get("ok") else "FAIL"
        parts.append(f"{ch.get('channel')}:{tag}")
    return "  ".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="briefbot",
        description="Config-driven digest bot: collect from sources -> "
                    "(optional LLM) summary -> push to channels.",
    )
    parser.add_argument("-c", "--config", required=True, help="path to YAML config")
    parser.add_argument("-j", "--job", help="run only the job with this name")
    parser.add_argument("--check", action="store_true", help="validate config and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the brief to stdout instead of pushing")
    parser.add_argument("--once", action="store_true",
                        help="run jobs once and exit (default when --loop is absent)")
    parser.add_argument("--loop", action="store_true",
                        help="keep running, executing jobs every --interval seconds")
    parser.add_argument("--interval", type=int, default=3600,
                        help="loop interval in seconds (minimum 60)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        cfg = load_config(args.config)
    except Exception as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    if args.check:
        print(f"OK: {len(cfg['jobs'])} job(s): "
              + ", ".join(j["name"] for j in cfg["jobs"]))
        return 0

    jobs = [j for j in cfg["jobs"] if not args.job or j["name"] == args.job]
    if not jobs:
        print(f"no job matched: {args.job!r}", file=sys.stderr)
        return 2

    state_path = (cfg.get("state") or {}).get("file", ".state/state.json")
    exit_code = 0
    while True:
        state = StateStore(state_path)
        if args.dry_run:
            # Preview only: use a throwaway copy so dedupe/snapshots are not persisted.
            state = state.transient()
        for job in jobs:
            result = run_job(cfg, job, state, dry_run=args.dry_run)
            print(_render(result))
            if result["status"] == "error" or any(
                not ch.get("ok") for ch in result.get("channels", [])
            ):
                exit_code = 1
        if not args.loop:
            return exit_code
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    sys.exit(main())
