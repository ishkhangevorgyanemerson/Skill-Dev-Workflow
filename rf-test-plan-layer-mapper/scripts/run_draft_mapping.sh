#!/usr/bin/env bash
set -euo pipefail
python scripts/analyze_plan.py --input "$1" --sheet "$2"
python scripts/apply_draft_steps.py --input "$1" --sheet "$2" --output "$3"
