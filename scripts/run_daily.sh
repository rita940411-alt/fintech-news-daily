#!/bin/zsh
set -u

PROJECT_DIR="$HOME/Projects/fintech-news-daily"
RUN_LOG_DIR="$HOME/Library/Logs"
RUN_LOG="$RUN_LOG_DIR/fintech-news-daily.log"

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export TZ="Asia/Taipei"
export LANG="zh_TW.UTF-8"

mkdir -p "$RUN_LOG_DIR"
exec >> "$RUN_LOG" 2>&1

echo "===== $(date '+%F %T %Z') START ====="

cd "$PROJECT_DIR" || exit 1

if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: working tree is not clean"
    git status --short
    exit 1
fi

LOCK_DIR="$RUN_LOG_DIR/fintech-news-daily.lock"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "Another daily run is already active. Exit."
    exit 0
fi

trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

CLAUDE_BIN="$(command -v claude || true)"

if [[ -z "$CLAUDE_BIN" ]]; then
    echo "ERROR: claude command not found"
    exit 1
fi

"$CLAUDE_BIN" -p "/fintech-news-daily" \
  --allowedTools "Read" "Write" "Edit" "Bash(python3 *)" "Bash(git *)"

if [[ $? -ne 0 ]]; then
    echo "ERROR: Claude Code failed"
    exit 1
fi

TODAY="$(date '+%F')"

for file in \
    "data/latest.json" \
    "data/archive/${TODAY}.json" \
    "data/audit/${TODAY}-candidates.json" \
    "docs/index.html" \
    "docs/archive/${TODAY}.html" \
    "logs/${TODAY}.log"
do
    if [[ ! -f "$file" ]]; then
        echo "ERROR: missing expected file: $file"
        exit 1
    fi
done

python3 src/validate_news.py data/latest.json
python3 src/validate_news.py --candidates "data/audit/${TODAY}-candidates.json"
python3 src/build_report.py

git add \
    data/latest.json \
    "data/archive/${TODAY}.json" \
    "data/audit/${TODAY}-candidates.json" \
    docs/index.html \
    "docs/archive/${TODAY}.html" \
    "logs/${TODAY}.log"

if git diff --cached --quiet; then
    echo "No generated changes. Nothing to commit."
    exit 0
fi

git commit -m "chore: update daily fintech news ${TODAY}"
git push origin main

echo "Daily report committed and pushed successfully."
echo "===== $(date '+%F %T %Z') SUCCESS ====="
