---
name: NI Test Plan Converter
slug: ni-test-plan-converter
version: 1.0.0
description: Generate PinMap XML, convert STIL patterns, compile digital patterns, and transform test plans into test sequences for NI Semiconductor Test System.
---

## When to Use

User needs to process semiconductor test artifacts for NI STS workflows:
- Channel map CSV needs conversion to PinMap XML
- STIL files need conversion to pattern source artifacts: `.digipatsrc`, `.digitiming`, and `.pinmap`
- Pattern source files need pin updates and compilation to `.digipat`
- Test plan Excel/CSV needs transformation to test sequences

## Core Rules

1. **No LLM calls** — all procedures are deterministic, rule-based algorithms
2. **Load only what you need** — each skill is a separate file; read on demand
3. **PinMap XML is the shared contract** — SKILLs 1, 3, and 4 all produce or consume PinMap XML
4. **Preserve order** — never reorder test cases, pins, or connections
5. **Sanitize pin names** — replace non-alphanumeric chars with `_`, strip trailing `_`, prefix digits
6. **Default output folder** — if the user does not specify an output directory, create a folder named `output` under the current workspace root and write all results there
7. **Folder = self-contained scope** — when the user provides a folder path as input, treat that folder as the sole source of all required files; never resolve files from other directories
8. **Validate required inputs before starting** — each sub-skill has mandatory files that must be present in the input folder before any processing begins; if any are missing, report the missing file(s) and stop
9. **Distinguish source vs compiled patterns** — `.digipatsrc` is a pattern source artifact; `.digipat` is a compiled pattern file. Do not claim `.digipat` output unless Skill 3 is run
10. **Do not infer business aliases** — never rename nets, pins, relays, or fields based on domain intuition or prior project history unless an explicit mapping file or written rule requires it
11. **Prefer deterministic scripts over reasoning** — when a skill-specific converter script exists, use it with explicit file paths instead of reconstructing the workflow from documentation alone
12. **Reply in the user's language** — all conversational responses (status updates, error messages, summaries, confirmations, and questions) must be written in the same language the user used; however, all generated output files, source code, scripts, variable names, XML content, and code comments must remain in **English**
13. **Resolve the correct Python interpreter** — do not assume bare `python` has the required packages; prefer `py -3.11` on Windows or verify the interpreter has required dependencies before running scripts
14. **Extension-first dispatch** — validate inputs by checking **file extensions and filenames only** (via directory listing); do **not** open or read file contents unless a skill explicitly requires it (e.g., distinguishing template vs plan by filename). When a deterministic script exists, pass the matched file paths directly to it
15. **Do not generate scripts on the fly** — every skill has a pre-built script; run it instead of writing Python, PowerShell, or any other code ad hoc. If a script is missing or broken, report the issue to the user rather than recreating the logic inline. This ensures even lightweight models can execute the skill reliably

## Extension-Based Dispatch

Before reading any skill doc, list the input folder and match files by extension to determine which skill applies. **Do not read file contents** at this stage.

| Extensions Found | Skill | Action |
|-----------------|-------|--------|
| `.csv` or `.xlsx` containing `Channel` in name | 1 | Run `channelmap_to_pinmap.ps1` |
| `.stil` + file named `Pinmap` | 2 | Run `stil_to_digipatsrc.py` / `digipatsrc_generator.py` |
| `.digipatsrc` + `.pinmap` | 3 | Run `patternsource_to_patternfile.py` (with `--compile` if compilation requested) |
| `.xlsx`/`.csv` + `.pinmap` + `.xlsx` with `Template` in name | 4 | Run `testplan_to_tsru.py` |

**Dispatch procedure:**

1. List the input folder contents (filenames and extensions only)
2. Match the above table top-to-bottom; first full match wins
3. If a script exists for the matched skill, run it with explicit paths — do not read the input files yourself
4. Only read file contents when the script is unavailable and manual processing is needed, or when disambiguation between candidate files requires peeking at headers

This avoids unnecessary file reads and keeps the agent fast and deterministic.

## Skill Chaining

Some skills can be chained in sequence. When the user requests an end-to-end workflow:

| Chain | Description |
|-------|-------------|
| 2 → 3 | Convert STIL to pattern source, then compile pattern sources to `.digipat` |
| 1 → 4 | Generate PinMap from channel map, then use it for test-plan conversion |

Each skill in a chain must complete its own verification checklist before the next skill begins. Do not skip intermediate validation.

## Required Inputs per Skill

| Skill | Required Files in Input Folder |
|-------|-------------------------------|
| 1 — ChannelMap → PinMap | Channel map file (`.xlsx` or `.csv`) |
| 2 — STIL → PatternSource | At least one `.stil` file **and** a `Pinmap` mapping file; outputs `.digipatsrc`, `.digitiming`, and `.pinmap` |
| 3 — PatternSource → PatternFile | At least one `.digipatsrc` file **and** a `.pinmap` XML file; outputs compiled `.digipat` |
| 4 — TestPlan → TestSequence | Test plan file (`.xlsx` or `.csv`), template Excel file (`.xlsx`), and PinMap XML (`.pinmap`); first check `Script/TSRU Modules/Generate Seq.cmd`, otherwise the user must provide a TSRU Modules folder |

## Quick Reference

| Skill | File | Description |
|-------|------|-------------|
| 1 | [ChannelMap_to_PinMap.md](ChannelMap_to_PinMap.md) | Generate PinMap XML from channel map CSV |
| 2 | [STIL_to_PatternSource.md](STIL_to_PatternSource.md) | Convert STIL files to pattern source artifacts: `.digipatsrc`, `.digitiming`, and `.pinmap` |
| 3 | [PatternSource_to_PatternFile.md](PatternSource_to_PatternFile.md) | Update pattern source files and compile `.digipat` binaries |
| 4 | [TestPlan_to_TestSequence.md](TestPlan_to_TestSequence.md) | Transform test plan into TSRU workbook, then generate test sequences if TSRU runtime and license are available |

> **Language rule reminder:** Respond to the user in their language. All file output stays in English.

| Reference | File |
|-----------|------|
| Channel map parsing & connection rules | [references/channelmap-rules.md](references/channelmap-rules.md) |
| STIL value mapping & timing tables | [references/stil-mapping.md](references/stil-mapping.md) |
| Pin matching algorithm | [references/pin-matching.md](references/pin-matching.md) |
| TSRU enrichment pipeline | [references/tsru-pipeline.md](references/tsru-pipeline.md) |
| TSRU field mapping & special fields | [references/tsru-field-rules.md](references/tsru-field-rules.md) |
