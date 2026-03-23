#!/bin/bash
# cron: */5 9-18 * * 1-5 /path/to/daily_monitor.sh
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export $(grep -v '^#' .env | xargs)
python -m src.main
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 완료"
