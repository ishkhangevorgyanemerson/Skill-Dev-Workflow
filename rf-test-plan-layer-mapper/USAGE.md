# Usage (v5.4)

## Environment setup (uv)

```bash
uv venv
uv sync
```

## Discover candidate sheets

```bash
uv run python scripts/discover_candidate_sheets.py --input workbook.xlsx
```

## Draft mapping

```bash
uv run python scripts/analyze_plan.py --input workbook.xlsx --sheet "LIMIT_Simplify"
uv run python scripts/apply_draft_steps.py --input workbook.xlsx --sheet "LIMIT_Simplify" --output workbook-draft.xlsx
```

`Spec_update` sheets with a semantic description column (for example `Test description` or `Test Item Description`) are handled with semantic grouping: rows with the same condition + mode + waveform + frequency + power + profile are merged into one step name.

## Correction loop (for styles with evaluation)

```bash
uv run python scripts/compare_with_evaluation.py --original original.xlsx --evaluation evaluation.xlsx --sheet "Test Time Evaluation" --output corrected.xlsx --delta-json delta.json
uv run python scripts/export_rulebook_update.py --delta delta.json --output learning-note.md
```

## PowerShell wrappers (Windows)

```powershell
./scripts/run_draft_mapping.ps1 -Input workbook.xlsx -Sheet "LIMIT_Simplify" -Output workbook-draft.xlsx
./scripts/run_correction_loop.ps1 -Original original.xlsx -Evaluation evaluation.xlsx -Sheet "Test Time Evaluation" -Output corrected.xlsx -LearningNote learning-note.md
```
