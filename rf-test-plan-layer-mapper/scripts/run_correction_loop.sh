#!/usr/bin/env bash
set -euo pipefail
DELTA_JSON="${5%.md}.json"
python scripts/compare_with_evaluation.py --original "$1" --evaluation "$2" --sheet "$3" --output "$4" --delta-json "$DELTA_JSON"
python scripts/export_rulebook_update.py --delta "$DELTA_JSON" --output "$5"
