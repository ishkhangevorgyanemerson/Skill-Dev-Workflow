param(
  [Parameter(Mandatory = $true)][string]$Original,
  [Parameter(Mandatory = $true)][string]$Evaluation,
  [Parameter(Mandatory = $true)][string]$Sheet,
  [Parameter(Mandatory = $true)][string]$Output,
  [Parameter(Mandatory = $true)][string]$LearningNote
)

$ErrorActionPreference = "Stop"
$deltaJson = [System.IO.Path]::ChangeExtension($LearningNote, ".json")

uv run python scripts/compare_with_evaluation.py --original "$Original" --evaluation "$Evaluation" --sheet "$Sheet" --output "$Output" --delta-json "$deltaJson"
uv run python scripts/export_rulebook_update.py --delta "$deltaJson" --output "$LearningNote"
