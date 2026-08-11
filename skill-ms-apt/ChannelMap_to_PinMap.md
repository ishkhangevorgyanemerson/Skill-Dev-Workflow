---
name: Channel Map to PinMap
slug: channelmap-to-pinmap
version: 1.0.0
description: Generate NI STS PinMap XML from a channel map CSV containing pin and relay tables.
---

## When to Use

User has a channel map CSV with pin/relay instrument assignments and needs a `.pinmap` XML file for NI Semiconductor Test System.

This skill should be executed as a deterministic transform of the provided channel map file.
Do **not** rely on semantic interpretation of net intent, tester usage, or prior project knowledge.

## Input / Output

- **In:** CSV with Pin Table (`Net Name`, `SITE1`, `SITE2`...) and Relay Table (`Net Name`, `Relay Number`, `SITE1`...)
- **Out:** `PinMap.pinmap` XML (schema: `http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd`)

## Pre-flight Validation

**Extension-only check** — list the folder and match by file extension. Do **not** open or read file contents at this stage.

Before any processing, verify that the input folder contains **all** of the following:

| # | Required File | How to Detect |
|---|--------------|---------------|
| 1 | Channel map file (`.xlsx` or `.csv`) | `glob("*.xlsx")` or `glob("*.csv")` returns ≥ 1 result |

If the channel map file is missing, **stop immediately** and report which file is absent. Do not fall back to files outside the given folder.

> **No content reading needed.** The converter script handles all CSV/Excel parsing internally. Just pass the matched file path to it.

## Output Folder

- If the user specifies an output directory, use it.
- If no output directory is given, create `{workspace_root}/output/pinmap/` and write the `PinMap.pinmap` there.

## Deterministic Procedure

When the user provides a channel map file or a folder containing one:

1. List the folder and find a `.csv` or `.xlsx` file (extension check only — do not read the file)
2. If the converter script exists, run it immediately with the matched path — **skip steps 3–9**
3. Only if the script is unavailable, proceed with manual processing:
4. Use only that provided file; do not consult sibling folders or existing `.pinmap` files for naming hints
5. Split the input into two sections:
  - Pin Table beginning with `Net Name,SITE1,SITE2,...`
  - Relay Table beginning with `RELAY,NET NAME,SITE1,SITE2,...`
4. Remove blank rows and exact duplicate rows while preserving first-seen order
5. Skip rows whose net name is `GND`
6. Sanitize pin names directly from the channel map net names
7. Build instruments only from device identifiers explicitly found in the SITE columns
8. Generate only these XML sections:
  - `Instruments`
  - `Pins`
  - `PinGroups`
  - `Relays`
  - `RelayGroups`
  - `Sites`
  - `Connections`
9. Write the PinMap XML to the requested output path
10. Verify the file exists and contains non-empty XML before reporting success

## Implementation

Use the deterministic converter script:

```powershell
powershell -ExecutionPolicy Bypass -File Script\channelmap_to_pinmap.ps1 `
  -InputCsv <channel_map.csv> `
  -OutputPinmap <output\PinMap.pinmap>
```

## Core Rules

1. **Parse two sections** — separate Pin Table and Relay Table from the CSV
2. **Group instruments** by `device_number` + `section` from cell values like `6571_S14_DIO_4`
3. **Name instruments** as `{device_type}_{device_number}_C1_S{section}` using the device mapping table
4. **Sanitize pin names** — non-alphanumeric → `_`, strip trailing `_`, prefix digits with device type, skip GND
5. **Group pins** by common name prefix, name groups `ALL_{prefix}`
6. **Combine relays** sharing a Net Name — `K1` + `K2` → `K1_2`; unique relays keep their name
7. **Sites are 0-indexed** — `SITE1` → `siteNumber="0"`
8. **Channel extraction** — `CH14` → `14`; trailing number `_4` → `4`; DAQ special: `{instrument}/ai{ch}` or `/ao{ch}`
9. **Relay control lines** — `K{number}` from `CH{number}` in relay cell values
10. **Folder = self-contained scope** — when the user provides a folder path, the channel map file must reside inside that folder; never search parent or sibling directories
11. **No semantic renaming** — do not rename `AVDD_HI` to `AVDD_DVDD`, `6571_SCK` to `SCLK_PPMU`, or any similar domain-specific alias unless an explicit mapping source is provided
12. **No inferred extra structures** — do not invent additional `RelayGroup`, `SystemPin`, or instrument entries not directly supported by the channel map input
13. **Preserve first-seen order** — instruments, pins, groups, relays, and connections should follow deterministic first appearance order after duplicate removal
14. **Do not generate code ad hoc** — the converter script `channelmap_to_pinmap.ps1` contains the full logic; run it instead of writing new code. If it is missing or broken, report the issue to the user

## What Not to Infer

Do **not** use AI judgment to guess:

- alternate business names for nets
- functional aliases such as `PPMU`, `DAQ`, `DVDD`, or `AVEE`
- extra system pins or system connections
- custom relay grouping beyond `All_Relays`
- hidden relationships from older project pinmaps

If the input file does not explicitly contain that information, omit it.

## Verification Checklist

Before responding, verify all of the following:

- output file exists
- output file is non-empty XML
- `Pins` contains only sanitized, non-`GND` DUT pins from the input
- `Sites` count matches the number of `SITE` columns
- every generated connection references an instrument declared in `Instruments`
- relay names were built only from relay rows in the input

If any check fails, report the failure and stop instead of claiming success.

## Response Guidance

Respond in the **user's language**. All generated files and script output remain in English.

Successful responses should include:

1. the validated input file path
2. the output file path
3. counts for generated pins and relays
4. a brief note that naming was derived directly from the channel map without semantic inference

## Quick Reference

| Topic | File |
|-------|------|
| Device mapping table & connection pseudocode | [references/channelmap-rules.md](references/channelmap-rules.md) |

## Output Structure

```xml
<PinMap schemaVersion="1.2">
  <Instruments/>  <!-- Step 2: device mapping table -->
  <Pins/>         <!-- Step 3: sanitized DUTPin names -->
  <PinGroups/>    <!-- Step 4: ALL_{prefix} groups -->
  <Relays/>       <!-- Step 5: combined SiteRelay names -->
  <RelayGroups/>  <!-- Step 6: single All_Relays group -->
  <Sites/>        <!-- Step 7: 0-indexed sites -->
  <Connections/>  <!-- Step 8: pin + relay connections -->
</PinMap>
```
