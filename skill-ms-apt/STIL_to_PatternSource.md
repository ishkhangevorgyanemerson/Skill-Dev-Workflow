---
name: STIL to Pattern Source
slug: stil-to-pattern-source
version: 1.0.0
description: Run the existing Python scripts to convert STIL files into NI STS-compatible digipatsrc, digitiming, and pinmap files.
---

## When to Use

User has `.stil` files and a signal-to-pin mapping file and needs NI STS-compatible pattern source, timing, and pin map outputs.
Prefer a **script-first** workflow: if the conversion scripts exist, run them with explicit arguments rather than re-implementing the parsing logic ad hoc.
If the user asks for “pattern files,” interpret that carefully:
- This skill produces pattern **source** artifacts: `.digipatsrc`, `.digitiming`, and `.pinmap`
- This skill does **not** compile `.digipatsrc` into `.digipat`
- If compiled binary pattern files are requested, complete this skill first, then hand off to [PatternSource_to_PatternFile.md](PatternSource_to_PatternFile.md)

## Input / Output

- **In:** Folder with `.stil` files + `Pinmap` CSV/text file (signal → tester pin mapping)
- **Out (per STIL file):** `.digipatsrc`, `.digitiming` XML, `.pinmap` XML

## Pre-flight Validation

**Extension-only check** — list the folder and match by file extension / filename. Do **not** open or read file contents.

Before any processing, verify that the input folder contains **all** of the following:

| # | Required File | How to Detect |
|---|--------------|---------------|
| 1 | At least one `.stil` file | `glob("*.stil")` returns ≥ 1 result |
| 2 | A `Pinmap` signal-mapping file | File named `Pinmap` (any extension or none) exists in the same folder |

If either is missing, **stop immediately** and report which file(s) are absent. Do not fall back to files outside the given folder.

> **No content reading needed.** The STIL conversion scripts parse `.stil` and `Pinmap` internally. Just pass the folder path to the batch generator or individual file paths to the CLI.

## Deterministic Procedure

When the user provides a folder path:

1. List the folder contents (extension/filename check only — do **not** read any `.stil` or `Pinmap` content)
2. Confirm the folder contains:
  - one or more `.stil` files
  - a file named `Pinmap`
3. If no output folder is specified, create:
  - `{workspace_root}/output/stil_pattern_source/`
4. **Run the existing scripts directly** — pass the folder path; the scripts handle all STIL parsing internally:

```python
from digipatsrc_generator import generate_pattern_source

generate_pattern_source(stil_folder="path/to/stil_files",
                output_folder="path/to/output/stil_pattern_source")
```

5. If the scripts are unavailable, only then implement the mapping manually using the STIL mapping reference
6. Verify that each input `.stil` file produced a subfolder named after its stem
7. Verify that each subfolder contains exactly these artifact types:
  - `{stem}.digipatsrc`
  - `{stem}.digitiming`
  - `{stem}.pinmap`
8. Report the generated file paths back to the user

## Output Folder

- If the user specifies an output directory, use it.
- If no output directory is given, create `{workspace_root}/output/stil_pattern_source/` and write results there.
- Each STIL file produces its own subfolder: `{output}/{stem}/` containing `.digipatsrc`, `.digitiming`, and `.pinmap`.

## Core Rules

1. **No LLM analysis needed** — this skill runs existing Python scripts directly
2. **Single file** — use `Script/stil_to_digipatsrc.py` CLI
3. **Batch folder** — call `generate_pattern_source(stil_folder, output_folder)` from `Script/digipatsrc_generator.py`
4. **Pinmap is required** — the `Pinmap` file must exist in the STIL folder (for batch) or be passed via `--pinmap` (for CLI)
5. **Output structure** — each STIL file gets its own subfolder under the output directory containing `.digipatsrc`, `.digitiming`, and `.pinmap`
6. **Folder = self-contained scope** — when the user provides a folder path, all required files (`.stil` and `Pinmap`) must reside inside that folder; never search parent or sibling directories
7. **Preserve file coverage** — process every `.stil` file found in the folder; do not skip or reorder files
8. **Do not over-promise output type** — never describe this skill as producing `.digipat` unless the compilation skill is also run
9. **Script-first execution** — prefer running the existing scripts with explicit file paths over re-implementing the STIL parsing logic
10. **Use the correct Python interpreter** — prefer `py -3.11` on Windows or verify the interpreter before running
11. **Do not generate code ad hoc** — the conversion scripts (`stil_to_digipatsrc.py`, `digipatsrc_generator.py`) contain the full logic; run them instead of writing new code. If they are missing or broken, report the issue to the user

## Single-File CLI

```
python Script/stil_to_digipatsrc.py <input.stil> <output.digipatsrc> --pinmap <Pinmap> [--tester NiSTS-6570] [-v]
```

| Flag | Purpose |
|------|---------|
| `--pinmap, -p` | Path to pinmap CSV (required) |
| `--tester, -t` | Target tester name (default: `NiSTS-6570`) |
| `--auto-output, -a` | Auto-name output from input filename |
| `--verbose, -v` | Print progress details |
| `--force, -f` | Overwrite without prompting |

## Batch Folder

```python
from digipatsrc_generator import generate_pattern_source

generate_pattern_source(stil_folder="path/to/stil_files",
                        output_folder="path/to/output")
```

This iterates every `.stil` in the folder, expects a `Pinmap` file in the same folder, and writes three output files per STIL into `output_folder/{stem}/`.

## Verification Checklist

After execution, validate all of the following before responding:

- The output root exists
- A subfolder exists for every input `.stil` stem
- Each subfolder contains:
  - one `.digipatsrc`
  - one `.digitiming`
  - one `.pinmap`
- No required input was resolved from outside the provided folder

If any expected artifact is missing, report the failed STIL file and stop instead of claiming success.

## Response Guidance

Respond in the **user's language**. All generated files and script output remain in English.

Successful responses should include:

1. Confirmation that the input folder passed validation
2. The output root used
3. A file-by-file list of generated artifacts
4. A brief note that `.digipat` compilation is a separate next step if requested

Example summary structure:

- Validated input folder contained `N` `.stil` file(s) and `Pinmap`
- Wrote outputs to `output/stil_pattern_source/`
- Generated:
  - `{stem}/{stem}.digipatsrc`
  - `{stem}/{stem}.digitiming`
  - `{stem}/{stem}.pinmap`
- If needed, next run Skill 3 to compile `.digipatsrc` into `.digipat`

## Failure Handling

Handle outcomes explicitly:

- **Missing `.stil` file** → stop and report the missing file
- **Missing `Pinmap` file** → stop and report the missing file
- **Script not found** → report that the conversion script is unavailable; do not attempt manual reimplementation without informing the user
- **Partial conversion** → if some `.stil` files succeed and others fail, report successful files and list failures separately
- **Import/dependency error** → report the missing package and suggest installation command

## Quick Reference

| Topic | File |
|-------|------|
| Internal mapping rules (value table, timing, drive formats) | [references/stil-mapping.md](references/stil-mapping.md) |

## Pipeline

```
STIL folder
  │
  ├─ stil_to_digipatsrc.py (single file CLI)
  │   or
  ├─ generate_pattern_source() (batch all .stil files)
  │
  └─ per file: STILParser → stil_data
                               ├─→ DigipatsrcGenerator(pinmap) → .digipatsrc
                               ├─→ DigitimingGenerator(pinmap) → .digitiming
                               └─→ PinmapGenerator(pinmap)     → .pinmap
```
