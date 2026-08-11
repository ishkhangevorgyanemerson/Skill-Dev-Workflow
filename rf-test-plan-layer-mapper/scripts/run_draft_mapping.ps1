param(
  [Parameter(Mandatory = $true)][string]$Input,
  [Parameter(Mandatory = $true)][string]$Sheet,
  [Parameter(Mandatory = $true)][string]$Output
)

$ErrorActionPreference = "Stop"
uv run python scripts/analyze_plan.py --input "$Input" --sheet "$Sheet"
uv run python scripts/apply_draft_steps.py --input "$Input" --sheet "$Sheet" --output "$Output"
