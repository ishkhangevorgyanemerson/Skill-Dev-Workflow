---
name: Pattern Source to Pattern File
slug: patternsource-to-patternfile
version: 1.0.0
description: Match pin names in digipatsrc declarations against PinMap XML and compile to digipat binary files.
---

## When to Use

User has `.digipatsrc` files and a `.pinmap` XML and needs to update pin names in pattern declarations then compile to `.digipat`.

Prefer treating “compile to digital pattern” as this skill:
- input pattern **source** files are `.digipatsrc`
- output compiled pattern **files** are `.digipat`
This skill depends on the NI Digital Pattern Compiler being installed locally. Verify compiler availability **before** processing any files.
## Input / Output

- **In:** Directory of `.digipatsrc` files + `.pinmap` XML file
- **Out:** Compiled `.digipat` files in output directory

## Pre-flight Validation

**Extension-only check** — list the folder and match by file extension. Do **not** open or read file contents at this stage.

Before any processing, verify that the input folder contains **all** of the following:

| # | Required File | How to Detect |
|---|--------------|---------------|
| 1 | At least one `.digipatsrc` file | `glob("*.digipatsrc")` returns ≥ 1 result |
| 2 | A `.pinmap` XML file | `glob("*.pinmap")` returns ≥ 1 result |

If either is missing, **stop immediately** and report which file(s) are absent. Do not fall back to files outside the given folder.

> **No manual Python required.** The `patternsource_to_patternfile.py` script handles PinMap parsing, pin matching, source updating, and optional compilation. Do **not** write ad-hoc Python code for these steps.

## Output Folder

- If the user specifies an output directory, use it.
- If no output directory is given, create `{workspace_root}/output/compiled_patterns/` and write the `.digipat` files there.
- Write updated `.digipatsrc` copies used for compilation under `{output}/updated_sources/` unless the user explicitly asks to modify the originals in place.

## Preferred Implementation

Use the deterministic converter script:

```text
.github/skills/skill-ms-apt/Script/patternsource_to_patternfile.py
```

**Pin update only** (no compilation):

```
py -3.11 Script/patternsource_to_patternfile.py ^
  --input-dir <folder_with_digipatsrc_and_pinmap> ^
  --output-dir <output/compiled_patterns>
```

**Pin update + compile:**

```
py -3.11 Script/patternsource_to_patternfile.py ^
  --input-dir <folder_with_digipatsrc_and_pinmap> ^
  --output-dir <output/compiled_patterns> ^
  --compile
```

**With explicit PinMap or compiler path:**

```
py -3.11 Script/patternsource_to_patternfile.py ^
  --input-dir <folder> ^
  --output-dir <output> ^
  --pinmap <explicit.pinmap> ^
  --compile ^
  --compiler-path "C:\Custom\Path\DigitalPatternCompiler.exe"
```

> **Do not create Python scripts on the fly.** If this script exists, run it. If it is missing or broken, report the issue — do not regenerate the logic ad hoc.

## Deterministic Procedure

When the user provides a folder path:

1. List the folder contents (extension check only — do not read files)
2. Confirm the folder contains:
  - one or more `.digipatsrc` files
  - one `.pinmap` file
3. **Run the script** — pass the folder path to `patternsource_to_patternfile.py` with `--compile` if compilation is requested — **skip steps 5–11**
4. If the script is unavailable, resolve the compiler executable **before** reading any file contents:

```
C:\Program Files\National Instruments\Digital Pattern Compiler\DigitalPatternCompiler.exe
```

5. If the compiler is missing, stop and report that compilation cannot proceed
6. Parse all `<DUTPin name="..."/>` values from the provided `.pinmap`
7. Process every `.digipatsrc` file in the folder, preserving file order
8. Update only the `pattern <name>(<pin_list>)` declaration pin list using the deterministic matching rules below
9. Preserve all non-declaration content exactly as-is
10. Write updated source copies to `{output}/updated_sources/`
11. Compile each updated `.digipatsrc` with the provided `.pinmap`
12. Verify that each source file produced a corresponding `.digipat`
13. Report the generated `.digipat` files and updated source copies back to the user

## Core Rules

1. **Extract pins from PinMap** — parse all `<DUTPin name="..."/>` from the XML
2. **Find pattern declarations** — lines matching `pattern <name>(<pin_list>)`
3. **Match pins deterministically** — use 4-priority matching (exact → component → prefix → substring)
4. **Write updated files safely** — replace only the pin list in declarations, preserve everything else
5. **Compile** — invoke `DigitalPatternCompiler.exe --outdir {out} --pinmap {pinmap}` per file
6. **Folder = self-contained scope** — when the user provides a folder path, all required files (`.digipatsrc` and `.pinmap`) must reside inside that folder; never search parent or sibling directories
7. **Do not modify originals by default** — write updated copies to the output folder unless the user explicitly requests in-place edits
8. **Preserve coverage and order** — process every `.digipatsrc` file found; do not skip or reorder files
9. **Require compiler availability** — do not claim success unless the NI compiler was found and executed successfully
10. **Script-first execution** — always run `Script/patternsource_to_patternfile.py` instead of writing Python on the fly; the script contains the full pin-matching and compilation logic
11. **Do not generate code ad hoc** — if the pre-built script exists, use it; if it is missing or broken, report the issue to the user instead of recreating the logic inline
12. **Compiler path resolution** — check the default path first; if not found, search `PATH` and common installation directories before giving up

## Quick Reference

| Topic | File |
|-------|------|
| Pin matching algorithm (4-priority strategy) | [references/pin-matching.md](references/pin-matching.md) |

## Pin Matching Priority

```
1. Exact match (case-insensitive)     "SDO" == "SDO"
2. Component match (split by _)       "SDO" in ["SDO", "PPMU"]
3. Prefix match                       "SDO" startswith "SDO_PPMU"
4. Substring match                    "SDO" in "nCS_SDO_PPMU"
5. No match → keep original
```

## Compiler Command

```
"C:\Program Files\National Instruments\Digital Pattern Compiler\DigitalPatternCompiler.exe"
  <source.digipatsrc> --outdir <output_dir> --pinmap <pinmap_path>
```

Equivalent supported form used in practice:

```
"C:\Program Files\National Instruments\Digital Pattern Compiler\DigitalPatternCompiler.exe"
  <source.digipatsrc> -outdir <output_dir> -pinmap <pinmap_path>
```

## Verification Checklist

After execution, validate all of the following before responding:

- The compiler executable was found
- The output root exists
- The updated source folder exists
- Every input `.digipatsrc` produced:
  - an updated `.digipatsrc` copy
  - a compiled `.digipat`
- The `.pinmap` used came from the provided folder only

If any expected compiled file is missing, report the failed source file and stop instead of claiming success.

## Response Guidance

Respond in the **user's language**. All generated files and script output remain in English.

Successful responses should include:

1. Confirmation that the input folder passed validation
2. Confirmation that the NI compiler was found
3. The output root used
4. A file-by-file list of generated `.digipat` outputs
5. A file-by-file list of updated `.digipatsrc` copies, if any were written

Example summary structure:

- Validated input folder contained `N` `.digipatsrc` file(s) and one `.pinmap`
- Found NI Digital Pattern Compiler
- Wrote compiled outputs to `output/compiled_patterns/`
- Wrote updated source copies to `output/compiled_patterns/updated_sources/`
- Generated `{stem}.digipat` for each input source file

## Failure Handling

Handle outcomes explicitly:

- **Missing `.digipatsrc` files** → stop and report the missing file
- **Missing `.pinmap` file** → stop and report the missing file
- **Compiler not found** → stop and report that the NI Digital Pattern Compiler is not installed; do not claim compilation success
- **Pin matching produced no changes** → still proceed with compilation; report that all pins already matched
- **Partial compilation failure** → report which files compiled successfully and which failed, with error details
- **Permission or path error** → report the specific error and suggest checking file paths and permissions
