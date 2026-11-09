# BriefBot — 3-day live validation report

**Window:** 2026-10-18 (baseline) to 2026-10-21 · **Mode:** plain digest, no API keys · **Schedule:** once daily, 18:00 local

This is the evidence behind the claim on the product page: three real jobs ran unattended for three days against live public sources, with zero errors. The raw run logs and the markdown briefs they produced are included in `day1-3-archive/` so you can audit every item.

## What was tested

| Job | Sources | What it proves |
|---|---|---|
| `cn-tech-digest` | RSS: sspai, Solidot, V2EX, OSChina (4 feeds) | New-item collection, dedupe across runs, plain digest rendering |
| `nextjs-stats-watch` | GitHub API (repo stats: stars / forks / issues) | Field snapshot + change diffing; silent when nothing changed |
| `nextjs-release-watch` | GitHub releases Atom feed | Release events; clean `skipped` status when there is no new release |

Configuration used: `validation/real-world.yaml` (included). No LLM key, no paid service.

## Results

| Date | cn-tech-digest | nextjs-stats-watch | nextjs-release-watch |
|---|---|---|---|
| 10-18 (baseline) | ok — 40 new items | ok — first snapshot | ok — 5 releases |
| 10-19 | ok — 32 items | ok — 3 field changes (stars +24 / forks +83 / issues +3) | skipped (no new release) |
| 10-20 | ok — 34 items | ok — 3 field changes (stars +18 / forks +39 / issues +9) | ok — 2 releases |
| 10-21 | ok — 33 items | ok — 3 field changes (stars −2 / forks −528 / issues +27) | ok — 2 releases |

- 9 scheduled job runs (3 jobs × 3 days): **0 errors**, no missing logs.
- 99 RSS items delivered in three daily briefs (32 + 34 + 33), with no duplicates across runs.
- 9 watched-field changes captured; on 10-19 no release existed and the job correctly stayed silent.
- A second run on the baseline day skipped everything already reported — dedupe is idempotent.

## One anomaly, reported not hidden

On 10-21 the `forks` field dropped by 528 (35,280 → 34,752). A direct GitHub API query that evening returned 34,774 — same order of magnitude — so this was a real upstream change (consistent with bulk fork cleanup), not a scraping error. BriefBot reported the diff as-is. Stars moved −2 the same day, also normal.

## What this does not prove

- It does not prove uptime of your machine or GitHub Actions; you own the scheduler.
- It does not benchmark LLM summary quality — plain mode was used deliberately, to show the product works with zero keys.
- Source availability changes; feeds can move or block bots. BriefBot fails per-source and keeps the remaining jobs running.

## Reproduce it

```bash
unzip briefbot-v1.0.2.zip && cd briefbot
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp validation/real-world.yaml config.yaml   # edit paths/sources as you like
python run.py -c config.yaml --dry-run      # preview, no messages sent
```

The offline self-test (`tests/smoke.yaml`) runs with no network and no keys.

_Generated 2026-10-21 as the closing summary of the validation window._
