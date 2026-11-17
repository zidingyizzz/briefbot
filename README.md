# BriefBot

[![CI](https://github.com/zidingyizzz/briefbot/actions/workflows/ci.yml/badge.svg)](https://github.com/zidingyizzz/briefbot/actions/workflows/ci.yml)

**Your own AI morning-brief bot — 15 minutes to set up, $0/month to run.**

One YAML file describes: *where to watch* (RSS feeds, web pages, JSON APIs) →
*what to say* (optional LLM summary in your own editorial voice) →
*where to deliver* (Telegram / email / Feishu / Server酱 / Bark / console).
Runs on your laptop, a $5 VPS, or **free on GitHub Actions** — no server required.

```
sources ──▶ state diff ──▶ digest ──▶ channels
(RSS /       (new items /    (LLM or     (Telegram /
 pages /      changed         plain)      email /
 JSON)        fields)                     Feishu)
```

## Written about

- [I spent a weekend on a bot that turns 40 minutes of feeds into a 40-second digest](https://dev.to/zidingyizzz/i-spent-a-weekend-on-a-bot-that-turns-40-minutes-of-feeds-into-a-40-second-digest-586a) — running BriefBot for free on GitHub Actions in about 5 minutes.

## Why you'll like it

- **One config, many use cases** — daily niche-news digest, competitor price
  watch, market/stock field monitoring, changelog alerts.
- **No vendor lock** — under 1,000 lines of readable Python, 4 dependencies.
  Read every line in one sitting.
- **Bring your own model** — any OpenAI-compatible endpoint works:
  OpenAI, DeepSeek, OpenRouter, Groq, or a local Ollama.
- **Works without any API key** — `mode: plain` sends a clean rule-based digest.
- **Remembers what it sent** — a tiny state file dedupes items and diffs watched
  fields, so you only hear about *new* things.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp config.example.yaml config.yaml        # then edit jobs
export OPENAI_API_KEY=sk-...              # optional (plain mode works without)
python run.py --config config.yaml --dry-run   # preview in console
python run.py --config config.yaml --once      # real run
```

Full walkthrough incl. Telegram bot setup and free GitHub Actions deployment:
**[docs/QUICKSTART.md](docs/QUICKSTART.md)**

## Configuration reference

### `llm:` (top level, optional)

| key | default | notes |
|---|---|---|
| `base_url` | `https://api.openai.com/v1` | any OpenAI-compatible endpoint |
| `api_key` | — | empty ⇒ plain digest fallback |
| `model` | `gpt-4o-mini` | e.g. `deepseek-chat` |

### job `sources:`

| type | key options | returns |
|---|---|---|
| `rss` | `url` (feed or local file), `limit` | one item per entry |
| `page_select` | `url`, `selectors` (CSS → field names) | one snapshot item with fields |
| `static_json` | `url` (API or local file), `list_path`, `uid_key`, `fields` (`"{tpl}"` per field), `limit` | one item per array row |

### job `digest:`

| key | default | notes |
|---|---|---|
| `mode` | `llm` | `llm` or `plain` |
| `only_new` | `true` | skip items already reported |
| `watch_changes` | `false` | diff `fields` against last snapshot (for `page_select`) |
| `only_changed` | `false` | stay silent when nothing changed |
| `max_items` | `30` | items shown in a plain digest; extras get a visible `(+N more)` note |
| `alert_after_failures` | `3` | consecutive source failures before the brief carries a ⚠️ health warning |
| `system_prompt` | built-in editor | override the LLM persona |

> Note: `watch_changes` keeps one snapshot per source. For a multi-row `static_json`
> source only the last row's fields get diffed — watch one row per source, or split
> rows into separate sources. (GitHub Actions cache eviction can also silently reset
> `.state/` — rare, but if a digest ever re-sends everything, that's why.)

### job `channels:`

| type | keys |
|---|---|
| `telegram` | `bot_token`, `chat_id` |
| `email` | `to` (+ top-level `smtp:` block) |
| `feishu` | `webhook` |
| `serverchan` | `send_key` (WeChat push via sct.ftqq.com) |
| `bark` | `device_key` (iOS push via the Bark app) |
| `file` | `path` (directory → one dated `.md` per day, or an explicit file; appends) |
| `stdout` | — (console; used by `--dry-run`) |

Secrets never live in the config — reference env vars with
`${VAR}` or `${VAR:-default}`. Subject templates support
`{job_name}` `{today}` `{items}` `{changes}`.

## Examples

- `config.example.yaml` — daily AI tech digest via Telegram
- `examples/price-watch.yaml` — page watcher with change alerts, **no LLM needed**
- `tests/smoke.yaml` — offline self-test (run it anywhere, zero keys)
- `validation/REPORT.md` — 3-day live validation: 9 runs, 0 errors, raw logs included

## CLI

```
python run.py -c CONFIG [--job NAME] [--check] [--dry-run] [--once]
                         [--loop --interval 3600] [-v]
```

## Alternatives (honest ones)

Different jobs, pick what fits:

- **[changedetection.io](https://github.com/dgtlmoon/changedetection.io)** — watches pages
  and pings you the moment something changes. Pick it if you want instant change
  alerts; BriefBot is the opposite rhythm: everything that changed today, edited
  into one morning message.
- **[RSSbrew](https://github.com/yinan-c/RSSbrew) / [RSS-GPT](https://github.com/yinan-c/RSS-GPT)** —
  filter feeds and attach AI summaries, but the output is still a feed/webpage,
  so you stay inside a reader. Pick them if you like reading in a reader.
- **Readless / briefing SaaS** — polished hosted briefings on a subscription.
  Pick one if you'd rather not touch a repo at all.
- Already running an AI agent (OpenClaw etc.)? Writing a skill for it may suit
  you better than a standalone bot — BriefBot is for people who prefer a small
  deterministic pipeline over an agent runtime.

## FAQ

**Delivered in China without a VPN?** Yes — Server酱 pushes to WeChat and Bark pushes to iOS; both need one key and zero servers.

**Does it need an LLM key?** No. `mode: plain` sends a clean bullet digest;
LLM mode just makes it read like your own newsletter.

**Will it re-send old items on GitHub Actions?** No — the bundled workflow
caches `.state/` between runs, so dedupe and field diffs survive.

**What if the cache evicts `.state/` anyway?** A daily run touches the cache daily, so this mostly happens after the schedule stops — GitHub disables scheduled workflows in public repos after 60 days without a push. The next run then re-sends up to `digest.max_items` items (default 30) once and rebuilds state. To skip the cache entirely, commit `.state/` to a branch and check it out in the workflow.

**Many jobs?** List as many as you like; each has its own sources and channels.

**Are secrets safe?** Keys come from environment variables or your local
config (both git-ignored), and delivery errors never echo request URLs — so a
failed send can't print your bot token into the logs.

**License** — MIT. Use it in commercial projects, fork it, rename it.

## The $19 kit (optional)

The source is MIT and fully usable as-is — clone it and run it, free forever.
If you'd rather skip the assembly, [getbriefbot.app](https://getbriefbot.app)
sells a one-time **$19 kit**: the packaged zip of the latest release, the
quick-start guide, and the 3-day live validation report (raw logs included),
with a 60-day refund window. Buying it funds continued development.
