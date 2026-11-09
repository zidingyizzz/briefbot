# Changelog

## v1.0.3 (2026-11-09)

Security hardening for the open-source release.

- **Fix: secrets can no longer leak into logs on a failed delivery.** The
  Telegram, ServerChan, Feishu and Bark APIs put the key in the request URL
  (bot token / send key / webhook id); `requests` embeds the full URL in its
  exception messages, so a failed send could print the key into logs or CI
  output. All push paths now raise URL-free errors (`network error (...)` /
  `HTTP <code> <reason>`). The same URL-free handling covers source fetching
  (`http_get`) and RSS parse errors, since public-repo Actions logs are
  world-readable and fork users may carry tokens in source URLs.
- **Fix: LLM digests treat feed content as untrusted data.** Items are framed
  between `<<<FEED` markers with an explicit system-prompt instruction not to
  follow instructions embedded in feed content (prompt-injection hardening;
  not a complete defense, but standard hygiene). LLM calls also use the
  URL-free error handling.

## v1.0.2 (2026-11-07)

Reliability and China-delivery release. Full audit: see repo history v1.0.1..v1.0.2.

- **Fix: no more lost items on delivery failure.** Items are only marked as
  seen after at least one channel accepts them; if every channel fails, the
  state is rolled back and the next run retries everything.
- **Fix: truncation is now visible.** Plain digests cap at 30 items by default
  but append a `(+N more not shown)` note; the cap is configurable via
  `digest.max_items`. (Subject counts no longer disagree with the body.)
- **Fix: Telegram long-message splitting.** Messages over the 4096-char API
  limit are split at newline boundaries instead of failing wholesale.
- **Fix: Feishu error detection.** Feishu reports errors inside HTTP 200
  responses; those now raise instead of silently "succeeding".
- **New: Server酱 channel** (`type: serverchan`) — WeChat push, one send key.
- **New: Bark channel** (`type: bark`) — iOS push, one device key.
- **New: source-health alerts.** A source failing `digest.alert_after_failures`
  runs in a row (default 3) adds a ⚠️ warning to the brief, and a warning-only
  brief is sent (with a non-zero exit code for monitors) if there is nothing
  else to report. Counters reset on recovery.
- **New: offline test suite** (26 tests) + GitHub Actions CI.
- Docs: channel tables, CN delivery guide in QUICKSTART, truthful line count.

Delivery semantics note: retries are at-least-once. If a multi-chunk Telegram
message fails halfway, the next run re-sends the whole brief (a chunk you
already received may repeat). Duplicates are preferred over silent loss.

## v1.0.1

Baseline as shipped in `dist/briefbot-v1.0.1.zip` (3-day live validation,
see `validation/REPORT.md`).
