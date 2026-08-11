---
name: Test Plan to TSRU
slug: testplan-to-tsru
version: 1.0.0
description: Transform test plan spreadsheets into test sequences by grouping, expanding, enriching, and mapping test cases to template worksheets, then generating sequence files via TSRU.
---

## When to Use

User has a test plan (Excel/CSV) with test cases, pins, and limits that needs conversion to a multi-sheet TSRU Excel workbook matching a provided template.

Prefer a **script-first** workflow so smaller models do not need to reason through the entire enrichment pipeline manually.
If the deterministic converter script is available, use it instead of re-implementing the mapping logic ad hoc.

## Input / Output

- **In:** Template Excel (defines worksheet headers), User Plan (CSV/Excel with test cases), PinMap XML (optional, for pin group lookup)
- **Out:** `TSRU_Generated_TestPlan.xlsx` with populated worksheets, deployed as `TestSpreadsheet.xlsx` under `TSRU Modules/` and sequence generated via `Generate Seq.cmd`

## Pre-flight Validation

**Extension-and-filename check** — list the folder and match by extension and filename pattern. Do **not** open or read file contents at this stage.

Before any processing, verify that the input folder (or workspace) contains **all** of the following:

| # | Required File | How to Detect |
|---|--------------|---------------|
| 1 | Test plan file (`.xlsx` or `.csv`) | Remaining `.xlsx`/`.csv` after template is identified |
| 2 | Template Excel file (`.xlsx`) | `.xlsx` file whose name contains `Template` |
| 3 | PinMap XML (`.pinmap`) | `glob("*.pinmap")` returns ≥ 1 result |
| 4 | `TSRU Modules/` folder with `Generate Seq.cmd` | First check `Script/TSRU Modules/`; otherwise user must provide an accessible folder |

If items 1-3 are missing, **stop immediately** and report which file(s) are absent.

> **No content reading needed.** Distinguish template from plan by filename (contains `Template`). The converter script handles all Excel parsing, PinMap lookup, and TSRU mapping internally. Just pass the matched file paths.

For item 4, resolve it in this order:

1. Check for `TSRU Modules/` under the skill Script folder:

```text
.github/skills/skill-ms-apt/Script/TSRU Modules/
```

2. Confirm that `Generate Seq.cmd` exists inside that folder
3. If found, use it without asking the user
4. If not found, stop and ask the user to provide the `TSRU Modules/` folder location

Do not guess alternate TSRU locations.

## Output Folder

- If the user specifies an output directory, use it.
- If no output directory is given, create `{workspace_root}/output/test_sequence/` and write `TSRU_Generated_TestPlan.xlsx` there, then deploy to `TSRU Modules/` as usual.

## Preferred Implementation

Use the deterministic converter script:

```text
.github/skills/skill-ms-apt/Script/testplan_to_tsru.py
```

Invoke it with explicit paths for:

- `--template`
- `--plan`
- `--pinmap`
- `--tsru-modules`
- `--output-dir`

This avoids relying on model judgment for workbook parsing, worksheet routing, and TSRU deployment behavior.

## TSRU Modules Resolution

Resolve the TSRU runtime folder before running generation:

1. Look for:

```text
.github/skills/skill-ms-apt/Script/TSRU Modules/
```

2. Require this command file:

```text
Generate Seq.cmd
```

3. If both exist, use that folder as the deployment and generation target
4. If either is missing, ask the user to provide the TSRU Modules path

This lookup is deterministic and should happen before any deployment step.

## Core Rules

1. **Pipeline order** — Read → Group → Expand → Enrich Names → Enrich Groups → Map → Post-Process → Save
2. **Group by sequence** — chunk consecutive tests with same `SequenceName`; leakage/continuity with shared pin groups stay together (5-10 items default, larger for leakage groups)
3. **Expand pin groups** — if `Pin` matches a PinGroup name AND `SequenceName` does NOT contain "ADC", create one test per pin in the group
4. **Test Name Base** — strip `_{Pin}` suffix, then measurement suffixes (`_OutputVoltage`, `_DNL`, etc.), then units (`(V)`, `MAX`)
5. **Pin group assignment** — look up pin in PinMap XML; if multiple groups contain it, pick the one with the most pins
6. **Worksheet routing** — normalize `SequenceName` and sheet names (lowercase, strip non-alphanumeric), match by containment; fallback to first sheet
7. **Column fill priority** — template fixed value → direct key match → semantic field mapping → special rules → empty string
8. **Special fields** — `Pins and Pin Groups` = `{"GroupName"}`; `Output Step` = `{SourceStep}_{TestNameBase}_{Group}`; `pinsOrPinGroups` uses template value only
9. **Post-process** — replace `[index]` placeholders with sequential counters; enforce Output Step format; normalize `Pins and Pin Groups` braces
10. **Resolve TSRU first** — first check `Script/TSRU Modules/` for `Generate Seq.cmd`; if absent, ask the user to provide the TSRU Modules path
11. **Deploy & generate** — copy the saved Excel to `TSRU Modules/TestSpreadsheet.xlsx`, then run `Generate Seq.cmd` from the resolved `TSRU Modules/` folder to produce the final `.seq` files
12. **Folder = self-contained scope** — when the user provides a folder path, all required files except the pre-resolved `Script/TSRU Modules/` runtime folder must reside inside that folder; never search parent or sibling directories
13. **Script-first execution** — if `Script/testplan_to_tsru.py` exists, use it as the canonical implementation path
14. **Partial-success handling** — if workbook generation succeeds but `Generate Seq.cmd` fails, report workbook success separately from sequence-generation failure
15. **License failures are external blockers** — if TSRU reports a missing TestStand/Semiconductor Module license, do not retry mapping logic; preserve the generated workbook and report the licensing blocker
16. **Do not generate code ad hoc** — the converter script `testplan_to_tsru.py` contains the full logic; run it instead of writing new code. If it is missing or broken, report the issue to the user

## Deterministic File Selection

To reduce ambiguity, resolve inputs using these rules:

1. **Template workbook**
  - prefer `.xlsx` files whose name contains `Template`
  - if exactly one such file exists, use it
2. **User test plan**
  - prefer `.xlsx` or `.csv` files in the same folder that are not the template workbook
  - if exactly one candidate remains, use it
3. **PinMap XML**
  - require exactly one `.pinmap` file in the provided folder
4. **TSRU Modules**
  - first use `Script/TSRU Modules/` if `Generate Seq.cmd` exists there

If any selection step yields multiple equally valid candidates, stop and ask the user instead of guessing.

## Deterministic Procedure

1. **List folder** — check extensions and filenames only (do **not** read file contents):
   - template: `.xlsx` with `Template` in name
   - plan: remaining `.xlsx` or `.csv`
   - PinMap: `.pinmap`
2. Resolve `TSRU Modules/` from `Script/TSRU Modules/`
3. If `TSRU Modules/Generate Seq.cmd` is not found, ask the user to provide the TSRU Modules folder path and stop
4. **Run the script** — pass matched paths to `Script/testplan_to_tsru.py` — **skip steps 6–13**
5. If the script is unavailable, only then follow the remaining manual pipeline steps
6. Read the test plan records
7. Parse PinMap groups
8. Group test cases
9. Expand pin-group based rows where allowed
10. Enrich derived fields
11. Route rows to template worksheets
12. Post-process worksheet rows
13. Save `TSRU_Generated_TestPlan.xlsx`
14. Copy it to the resolved TSRU folder as `TestSpreadsheet.xlsx`
15. Run `Generate Seq.cmd`
16. If TSRU generation fails after workbook creation, preserve and report the workbook path
17. Verify that sequence output files were produced before reporting full success

## Failure Handling

Handle outcomes explicitly:

- **Missing input file** → stop and report the missing file
- **Multiple candidate template or plan files** → ask the user to choose
- **Missing `Generate Seq.cmd`** → ask the user for TSRU Modules location
- **Workbook generated, TSRU failed** → report partial success and preserve the workbook
- **License warning/failure from TSRU** → report external licensing blocker; do not claim `.seq` success

## Response Guidance

Respond in the **user's language**. All generated files and script output remain in English.

Successful or partial-success responses should include:

1. the selected template path
2. the selected test plan path
3. the selected PinMap path
4. the TSRU Modules path used
5. whether workbook generation succeeded
6. whether `.seq` generation succeeded
7. any external blocker such as missing license

## Quick Reference

| Topic | File |
|-------|------|
| Enrichment pipeline pseudocode (group, expand, enrich) | [references/tsru-pipeline.md](references/tsru-pipeline.md) |
| Field mapping table, special field rules, post-processing | [references/tsru-field-rules.md](references/tsru-field-rules.md) |

## Pipeline Overview

```
User Plan + PinMap XML
  │
  ├─ B. Group test cases (by sequence, leakage/continuity rules)
  │
  ├─ C. Expand pin groups (one test per pin, skip ADC)
  │
  ├─ D. Enrich Test Name Base (strip suffixes/units)
  │
  ├─ E. Enrich Pin Groups (lookup largest enclosing group)
  │
  ├─ F. Map to template worksheets (route + fill columns)
  │
  ├─ G. Post-process (index placeholders, Output Step, formatting)
  │
  ├─ H. Save multi-sheet Excel
  │
  └─ I. Deploy to TSRU Modules & run Generate Seq.cmd
```
