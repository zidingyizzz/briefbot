#!/usr/bin/env bash
# Build the distributable zip from the current HEAD (git-tracked files only).
# Usage: scripts/build.sh            -> dist/briefbot-v<version>.zip
set -euo pipefail
cd "$(dirname "$0")/.."

ver=$(python3 - <<'PY'
import re
print(re.search(r'__version__ = "(.+?)"',
                open("briefbot/__init__.py", encoding="utf-8").read()).group(1))
PY
)

mkdir -p dist
out="dist/briefbot-v${ver}.zip"
git archive --format=zip --prefix="briefbot/" --output="$out" HEAD
echo "built $out"
unzip -l "$out" | tail -3
