#!/bin/bash
# BriefBot 3-day real-world validation runner.
# Installed via the system scheduler (one run per day). Self-disables on/after 2026-10-22.
set -u

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
END_DATE=20261022
TODAY=$(date +%Y%m%d)

if [ "$TODAY" -ge "$END_DATE" ]; then
    echo "$(date '+%F %T') validation window closed — skipping (you may remove this cron entry)" \
        >> "$PROJECT/validation/logs/cron.log"
    exit 0
fi

cd "$PROJECT" || exit 1
mkdir -p validation/logs
exec python3 run.py \
    --config validation/real-world.yaml --once \
    >> "validation/logs/run-$(date +%Y%m%d).log" 2>&1
