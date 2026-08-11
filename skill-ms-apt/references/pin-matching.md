# Pattern Source to Pattern File — Pin Matching Algorithm

This reference describes the deterministic pin-update step used before compiling `.digipatsrc` pattern source files into `.digipat` files.

## Execution Notes

- Treat the user-provided folder as the complete input scope
- Read `.digipatsrc` and `.pinmap` only from that folder
- Do **not** modify the original `.digipatsrc` files by default
- Write updated source copies to an output folder before compilation
- Do not claim success unless the NI Digital Pattern Compiler completes and the expected `.digipat` files exist

---

## PinMap XML Parsing

```python
import xml.etree.ElementTree as ET

tree = ET.parse(pinmap_path)
root = tree.getroot()
ns = {'pm': 'http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd'}

pinmap_pins = []
for dut_pin in root.findall('.//pm:DUTPin', ns):
    pinmap_pins.append(dut_pin.get('name'))
```

---

## Pattern Declaration Parsing

Find lines matching: `pattern <name>(<pin_list>)`

```python
import re

for line in lines:
    match = re.match(r'(pattern\s+\w+\s*\()([^)]+)(\))', line.strip())
    if match:
        prefix = match.group(1)       # "pattern ADDA_PU("
        pin_list = match.group(2)      # "CS, SCLK, SDI, SDO"
        suffix = match.group(3)        # ")"
        original_pins = [p.strip() for p in pin_list.split(',')]
```

    Only replace the pin list inside the declaration. Preserve all other lines and formatting exactly as-is.

---

## `find_best_pin_match` — 4-Priority Strategy

For each pin in the pattern declaration, find the best matching pin from the PinMap:

```python
def find_best_pin_match(pattern_pin, pinmap_pins):
    """
    Returns the best-matching PinMap pin for a given pattern pin.
    Tries 4 strategies in order; returns original if none match.
    """
    pattern_pin_lower = pattern_pin.lower()

    # Priority 1: Exact match (case-insensitive)
    for pm_pin in pinmap_pins:
        if pm_pin.lower() == pattern_pin_lower:
            return pm_pin

    # Priority 2: Component match
    # Split PinMap pin by '_' and check if pattern pin matches any component
    for pm_pin in pinmap_pins:
        components = pm_pin.lower().split('_')
        if pattern_pin_lower in components:
            return pm_pin

    # Priority 3: Prefix match
    # PinMap pin starts with pattern pin (case-insensitive)
    for pm_pin in pinmap_pins:
        if pm_pin.lower().startswith(pattern_pin_lower):
            return pm_pin

    # Priority 4: Substring match
    # Pattern pin appears anywhere inside PinMap pin
    for pm_pin in pinmap_pins:
        if pattern_pin_lower in pm_pin.lower():
            return pm_pin

    # No match found — keep original pin name unchanged
    return pattern_pin
```

---

## Matching Examples

| Pattern Pin | PinMap Pins Available            | Match       | Priority Used |
|-------------|----------------------------------|-------------|---------------|
| `SDO`       | `SDO`, `SDO_PPMU`               | `SDO`       | 1 (exact)     |
| `SDO`       | `SDO_PPMU`, `SCLK_PPMU`         | `SDO_PPMU`  | 2 (component) |
| `CS`        | `nCS_PPMU`, `SCLK_PPMU`         | `nCS_PPMU`  | 4 (substring) |
| `SCLK`      | `SCLK_PPMU`, `SDI_PPMU`         | `SCLK_PPMU` | 2 (component) |
| `MISO`      | `SDO_PPMU`, `SDI_PPMU`          | `MISO`      | 5 (no match)  |

---

## Full Update Workflow

```python
def update_pattern_file(source_path, updated_path, pinmap_pins):
    with open(source_path, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        match = re.match(r'(pattern\s+\w+\s*\()([^)]+)(\))', line.strip())
        if match:
            prefix = match.group(1)
            original_pins = [p.strip() for p in match.group(2).split(',')]
            suffix = match.group(3)

            new_pins = [find_best_pin_match(p, pinmap_pins) for p in original_pins]
            updated_line = f"{prefix}{', '.join(new_pins)}{suffix}\n"
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    with open(updated_path, 'w') as f:
        f.writelines(updated_lines)
```

Recommended behavior:

- `source_path` is the original input file
- `updated_path` is a copy in `{output}/updated_sources/`
- compile from `updated_path`, not from the original source file

---

## End-to-End Procedure

1. Validate the input folder contains:
   - one or more `.digipatsrc` files
   - one `.pinmap` file
2. Resolve the compiler executable:

```
C:\Program Files\National Instruments\Digital Pattern Compiler\DigitalPatternCompiler.exe
```

3. If the compiler is missing, stop immediately
4. Parse all PinMap DUT pins
5. Process each `.digipatsrc` file in folder order
6. Write updated copies to `{output}/updated_sources/`
7. Compile each updated file to `{output}/`
8. Verify that each input source produced a corresponding `.digipat`

---

## Compilation

After updating pin names, compile each file:

```
"C:\Program Files\National Instruments\Digital Pattern Compiler\DigitalPatternCompiler.exe"
  <source.digipatsrc>
  --outdir <output_directory>
  --pinmap <pinmap_path>
```

Equivalent supported form:

```
"C:\Program Files\National Instruments\Digital Pattern Compiler\DigitalPatternCompiler.exe"
    <source.digipatsrc>
    -outdir <output_directory>
    -pinmap <pinmap_path>
```

Output: `{stem}.digipat` in the specified output directory.

---

## Verification Checklist

Before reporting success, confirm:

- the compiler executable was found
- each input `.digipatsrc` produced an updated source copy
- each input `.digipatsrc` produced a compiled `.digipat`
- the `.pinmap` used came from the same provided folder
