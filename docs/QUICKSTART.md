# BriefBot Quick Start (5–15 minutes)

## 1. Install (2 min)

```bash
cd briefbot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Requires Python 3.10+.

## 2. First taste — offline smoke test (1 min, zero keys)

```bash
.venv/bin/python run.py --config tests/smoke.yaml --once
# run again → "[smoke] skipped  reason=no new items" (dedupe works)
```

## 3. Configure your first digest (5 min)

```bash
cp config.example.yaml config.yaml
```

Edit the job: swap in your favorite RSS feeds, tweak the `system_prompt`,
and set the subject line.

Preview without sending anything:

```bash
.venv/bin/python run.py --config config.yaml --dry-run
```

## 4. Wire up Telegram (3 min, optional)

1. In Telegram, talk to **@BotFather** → `/newbot` → copy the token.
2. Send any message to your new bot (it needs a chat to write to).
3. Get your chat id: open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and read `chat.id`.
4. Export and run:

```bash
export TELEGRAM_BOT_TOKEN="123:abc"
export TELEGRAM_CHAT_ID="456"
.venv/bin/python run.py --config config.yaml --once
```

(For email instead: fill the `smtp:` block and use the `email` channel.
For Feishu: create a custom bot webhook and use the `feishu` channel.)

**In mainland China without Telegram?** Two one-key channels work out of the box:
- **Server酱** (WeChat push): grab a send key at <https://sct.ftqq.com>, then
  `- type: serverchan` + `send_key: ${SERVERCHAN_SEND_KEY}`.
- **Bark** (iOS push): install the Bark app, copy the key on its homepage, then
  `- type: bark` + `device_key: ${BARK_DEVICE_KEY}`.

## 5. Run it free on GitHub Actions (5 min, no server)

1. Push this folder to a **private** GitHub repo (secrets stay env-only,
   but private is the safe default).
2. In repo **Settings → Secrets and variables → Actions** add:
   - Secrets: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - Optional Variables: `OPENAI_BASE_URL`, `OPENAI_MODEL`
3. The bundled workflow `.github/workflows/briefbot.yml` runs daily at
   08:00 Beijing time and caches `.state/` so nothing is re-sent.
   Change the `cron:` line to your schedule, or trigger it manually from the
   **Actions** tab (`workflow_dispatch`).

## 6. Local scheduling alternative

macOS/Linux crontab, daily at 08:00:

```
0 8 * * * cd /path/to/briefbot && .venv/bin/python run.py -c config.yaml --once
```

## Troubleshooting

- **`config error: ...`** — usually a missing env var; check `--check`.
- **Telegram 400** — the bot auto-retries as plain text; usually caused by
  unbalanced markdown in the LLM output.
- **A source fails** — the job still runs with the remaining sources;
  check the `error=` line in the run output.
