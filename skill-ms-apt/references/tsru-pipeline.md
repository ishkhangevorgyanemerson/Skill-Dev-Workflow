# TSRU Pipeline — Enrichment Pseudocode

This reference is intentionally **deterministic**.

Preferred approach:

1. resolve inputs explicitly
2. run `Script/testplan_to_tsru.py`
3. only reason through the pseudocode below if the script is unavailable or needs repair

Smaller models should avoid reconstructing the full pipeline from memory when the script already exists.

---

## Deterministic Input Resolution

Use these rules before any pipeline logic:

- template workbook: prefer filename containing `Template`
- user plan: prefer remaining `.xlsx`/`.csv` file in the same folder
- PinMap: require exactly one `.pinmap`
- TSRU runtime: first check `.github/skills/skill-ms-apt/Script/TSRU Modules/Generate Seq.cmd`

If a rule yields multiple equally valid candidates, stop and ask the user.

---

## Preferred Command

```text
py -3.11 .github/skills/skill-ms-apt/Script/testplan_to_tsru.py \
  --template <template.xlsx> \
  --plan <user_plan.xlsx|csv> \
  --pinmap <PinMap.pinmap> \
  --tsru-modules <Script/TSRU Modules> \
  --output-dir <output/test_sequence>
```

---

## A. Parse Pin Groups from PinMap XML

```python
import xml.etree.ElementTree as ET
import re

def parse_pin_groups_from_xml(pinmap_xml_string):
    if not pinmap_xml_string:
        return {}

    if not pinmap_xml_string.strip().startswith('<?xml'):
        pinmap_xml_string = (
            '<root xmlns="http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd">'
            f'{pinmap_xml_string}</root>'
        )

    try:
        root = ET.fromstring(pinmap_xml_string)
        ns = {'pm': 'http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd'}
        groups = {}
        for pg in root.findall('.//pm:PinGroup', ns):
            name = pg.get('name')
            pins = [pr.get('pin') for pr in pg.findall('pm:PinReference', ns)]
            groups[name] = pins
        return groups
    except ET.ParseError:
        groups = {}
        for m in re.finditer(r'<PinGroup\s+name="([^"]+)">(.*?)</PinGroup>', pinmap_xml_string, re.DOTALL):
            name = m.group(1)
            pins = re.findall(r'<PinReference\s+pin="([^"]+)"', m.group(2))
            groups[name] = pins
        return groups
```

---

## B. Group Test Cases

**Goal:** Chunk consecutive test cases by sequence similarity; keep leakage/continuity tests sharing a pin group together.

```python
def group_test_cases(records, pinmap_xml):
    pin_groups = parse_pin_groups_from_xml(pinmap_xml)
    chunks = []
    current_chunk = []

    for i, record in enumerate(records):
        current_chunk.append(record)

        if len(current_chunk) < 5:
            continue

        if i + 1 < len(records):
            next_record = records[i + 1]
            key = get_grouping_key(record)
            next_key = get_grouping_key(next_record)

            if key == next_key and key != "":
                if is_leakage_or_continuity(record):
                    if same_pin_group(record.get("Pin", ""), next_record.get("Pin", ""), pin_groups):
                        continue

                if len(current_chunk) < 10:
                    continue

        chunks.append(current_chunk)
        current_chunk = []

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def get_grouping_key(record):
    for k in ["StepName", "SequenceName", "TestName"]:
        if k in record and record[k]:
            return str(record[k]).strip()
    return ""


def is_leakage_or_continuity(record):
    name = str(record.get("TestName", "") or record.get("SequenceName", "")).lower()
    return "leakage" in name or "continuity" in name


def same_pin_group(pin_a, pin_b, pin_groups):
    for _, pins in pin_groups.items():
        if pin_a in pins and pin_b in pins:
            return True
    return False
```

Important:

- preserve original record order
- grouping changes chunk boundaries only; it must not reorder tests

---

## C. Expand Pin Groups

**Goal:** When a test's `Pin` matches a PinGroup name and `SequenceName` does not contain `ADC`, create one record per pin in that group.

```python
def expand_test_cases(chunk, pinmap_xml):
    pin_groups = parse_pin_groups_from_xml(pinmap_xml)
    expanded = []

    for record in chunk:
        pin = record.get("Pin", "")
        sequence = str(record.get("SequenceName", ""))
        is_group = pin in pin_groups
        is_not_adc = "ADC" not in sequence.upper()

        if is_group and is_not_adc:
            group_pins = pin_groups[pin]
            base_num = record.get("TestNumber", 0)

            for j, individual_pin in enumerate(group_pins):
                new_rec = dict(record)
                new_rec["TestName"] = f"{record['TestName']}_{individual_pin}"
                new_rec["Pin"] = individual_pin
                new_rec["TestNumber"] = base_num + j
                expanded.append(new_rec)
        else:
            expanded.append(dict(record))

    return expanded
```

Expansion rules:

- expand only when `Pin` exactly matches a PinGroup name
- do not expand ADC sequence rows
- preserve first-seen group pin order from the PinMap XML

---

## D. Enrich Test Name Base

**Goal:** Derive a canonical `Test Name Base` by removing pin suffixes, measurement suffixes, and units.

```python
import re

MEASUREMENT_SUFFIXES = [
    "_OutputVoltage", "_InputVoltage", "_Leakage",
    "_DNL", "_INL", "_OffsetError", "_GainError",
    "_InputResistance"
]

UNIT_PATTERNS = [
    r'\(V\)', r'\(uA\)', r'\(LSB\)', r'\(mA\)', r'\(mV\)',
    r'\s+MAX$', r'\s+MIN$', r'_MAX$', r'_MIN$'
]


def enrich_test_name_base(records):
    for record in records:
        test_name = str(record.get("TestName", ""))
        pin = str(record.get("Pin", ""))
        base = test_name

        if pin and base.endswith(f"_{pin}"):
            base = base[: -len(f"_{pin}")]

        for suffix in MEASUREMENT_SUFFIXES:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break

        for pattern in UNIT_PATTERNS:
            base = re.sub(pattern, '', base)

        base = base.replace(" ", "_").strip("_")

        if not base:
            base = test_name.replace(" ", "_").strip("_")

        record["Test Name Base"] = base

    return records
```

---

## E. Enrich Pin Groups

**Goal:** Assign the largest enclosing PinGroup for each test pin.

```python
def enrich_pin_groups(records, pinmap_xml):
    pin_groups = parse_pin_groups_from_xml(pinmap_xml)

    pin_to_groups = {}
    for group_name, pins in pin_groups.items():
        for pin in pins:
            pin_to_groups.setdefault(pin, []).append((group_name, len(pins)))

    for record in records:
        pin = str(record.get("Pin", "")).strip()

        if not pin:
            record["Pin Groups"] = ""
            continue

        if pin in pin_to_groups:
            candidates = pin_to_groups[pin]
            candidates.sort(key=lambda x: x[1], reverse=True)
            record["Pin Groups"] = candidates[0][0]
        else:
            record["Pin Groups"] = pin

    return records
```

If no group contains the pin, use the pin itself.
Do not guess alternate business aliases.

---

## Execution Outcome Rules

There are two distinct success levels:

1. **Workbook success**
   - `TSRU_Generated_TestPlan.xlsx` exists and is populated
2. **Sequence success**
   - `Generate Seq.cmd` completes successfully and produces `.seq` output

If level 1 succeeds and level 2 fails, report **partial success**.
Do not mark the full skill as fully successful.

Typical external blocker:

- missing or inactive TestStand / Semiconductor Module license required by TSRU

When this happens, preserve the generated workbook and report the blocker explicitly.
