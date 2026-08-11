---
name: rf-test-plan-layer-mapper
description: Draft and correct Layer 1 -> Layer 2 mappings for RF test plan spreadsheets. Ask the user which sheet is the main test plan sheet when the workbook has multiple sheets or is ambiguous. If the chosen sheet does not already have a mapping column, create one automatically. v5.4 adds formal LIMIT_RF support for LIMIT_Simplify workbooks.
allowed-tools:
  - Read
  - Write
  - Edit
  - MultiEdit
  - Bash
compatibility: Python 3.12+ with openpyxl (managed by uv).
license: Proprietary
---

# RF Test Plan Layer Mapper v5.4

## Operating rules
1. Run candidate-sheet discovery or ask the user which sheet is the main test plan sheet when the workbook has multiple sheets or the structure is ambiguous.
2. Use `--sheet` in scripts to explicitly target the selected sheet.
3. If the selected sheet has no mapping column, create one in a style-aware location.
4. For E6 workbooks, create three columns after `Test Name`: `NI Evaluation`, `TestTime_1site`, `TestTime_4Site` (while still accepting legacy `NI Evalution`).
5. For LIMIT_RF workbooks (e.g. `LIMIT_Simplify`), create one column after `Item`: `Predicted Test Step`.
6. Draft first, then compare with evaluation if available.
7. For `Spec_update` style sheets with a semantic description column, derive step names by semantic grouping (same condition + mode + waveform + frequency + power + profile), instead of fixed LIMIT_RF script mapping.

## Runtime setup
1. Create virtual environment with `uv venv`.
2. Install locked dependencies with `uv sync`.
3. Run scripts via `uv run python ...` to ensure the managed runtime is used.
