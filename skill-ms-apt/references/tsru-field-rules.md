# TSRU Field Mapping, Special Fields & Post-Processing

## F. Map to TSRU Template

### F.1 Worksheet Selection

```python
import re

def normalize(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def select_worksheet(record, template_data):
    """
    Match test to worksheet by SequenceName ↔ sheet name containment.
    Fallback: first worksheet.
    """
    sequence = str(record.get("SequenceName", record.get("StepName", "")))
    normalized_seq = normalize(sequence)

    best_match = None
    best_score = 0

    for sheet_name in template_data:
        normalized_sheet = normalize(sheet_name)
        if normalized_seq in normalized_sheet or normalized_sheet in normalized_seq:
            score = len(set(normalized_seq) & set(normalized_sheet))
            if score > best_score:
                best_score = score
                best_match = sheet_name

    return best_match or list(template_data.keys())[0]
```

### F.2 Row Building

```python
FIELD_MAP = {
    "Test Name":   ["TestName", "Test Name", "Test"],
    "Pin":         ["Pin"],
    "L_Limit":     ["Low Limit", "LowLimit", "Min", "Low"],
    "Low Limit":   ["Low Limit", "LowLimit", "Min", "Low"],
    "H_Limit":     ["High Limit", "HighLimit", "Max", "High"],
    "High Limit":  ["High Limit", "HighLimit", "Max", "High"],
    "Unit":        ["Unit", "Units"],
    "Test Number": ["TestNumber", "Test Number"],
}


def build_row(record, target_headers, template_rows):
    """
    Build one output row.

    Priority chain per column:
      1. Template fixed value (non-empty value from template row)
      2. Direct key match from record
      3. Semantic field mapping via FIELD_MAP
      4. Special field rules (apply_special_fields)
      5. Empty string fallback
    """
    template_defaults = template_rows[0] if template_rows else {}
    row = {}

    for header in target_headers:
        value = ""

        # Priority 1: template fixed value
        tpl_val = str(template_defaults.get(header, "")).strip()
        if tpl_val and tpl_val not in ("", "nan", "None"):
            value = tpl_val
        else:
            # Priority 2: direct key match
            if header in record and str(record[header]).strip():
                value = str(record[header])
            else:
                # Priority 3: mapped key match
                for key in FIELD_MAP.get(header, []):
                    if key in record and str(record[key]).strip():
                        value = str(record[key])
                        break

        row[header] = value

    # Priority 4: special fields
    apply_special_fields(row, record, target_headers)
    return row
```

---

## F.3 Special Field Generation

```python
def apply_special_fields(row, record, target_headers):
    test_name_base = record.get("Test Name Base", "")
    pin_groups     = record.get("Pin Groups", "")
    source_step    = row.get("Source Step", "")

    # ── Pins and Pin Groups ──
    if "Pins and Pin Groups" in target_headers:
        if pin_groups:
            clean = pin_groups.strip('{} "\' ')
            row["Pins and Pin Groups"] = f'{{"{clean}"}}'
        else:
            row["Pins and Pin Groups"] = ""

    # ── Output Step ──
    if "Output Step" in target_headers:
        if source_step and test_name_base:
            clean_group = pin_groups.strip('{} "\' ') if pin_groups else ""
            if clean_group:
                row["Output Step"] = f"{source_step}_{test_name_base}_{clean_group}"
            else:
                row["Output Step"] = f"{source_step}_{test_name_base}"

    # ── pinsOrPinGroups ──
    # CRITICAL: use template value ONLY, do NOT override with calculated pin groups
    if "pinsOrPinGroups" in target_headers:
        pass  # keep whatever was set from template

    # ── Pin ──
    if "Pin" in target_headers:
        pin_val = record.get("Pin", "")
        if pin_val:
            row["Pin"] = pin_val
```

---

## G. Post-Processing

Applied after all chunks are mapped.

```python
def post_process(merged_results, enriched_chunks):
    # Build lookup: TestName → Test Name Base
    tnb_lookup = {}
    for chunk in enriched_chunks:
        for rec in chunk:
            if "TestName" in rec and "Test Name Base" in rec:
                tnb_lookup[rec["TestName"]] = rec["Test Name Base"]

    for sheet_name, rows in merged_results.items():
        variable_counters = {}

        for row in rows:
            # ── Normalize Pins and Pin Groups braces ──
            if "Pins and Pin Groups" in row:
                val = str(row["Pins and Pin Groups"]).strip()
                if val:
                    clean = val.strip('{} "\'')
                    row["Pins and Pin Groups"] = f'{{"{clean}"}}' if clean else ""

            # ── Enforce Output Step format ──
            if "Output Step" in row:
                base = tnb_lookup.get(row.get("Test Name", ""), "")
                source_step = str(row.get("Source Step", "")).strip()

                if base and source_step:
                    group = str(row.get("Pins and Pin Groups", "")).strip().strip('{} "\'')
                    if group:
                        row["Output Step"] = f"{source_step}_{base}_{group}"
                    else:
                        row["Output Step"] = f"{source_step}_{base}"

            # ── Replace [index] placeholders ──
            for key, value in row.items():
                if isinstance(value, str) and "[index]" in value:
                    match = re.search(r"(.*?)\[index\]", value)
                    if match:
                        prefix = match.group(1)
                        if prefix not in variable_counters:
                            variable_counters[prefix] = 0
                        idx = variable_counters[prefix]
                        row[key] = value.replace("[index]", f"[{idx}]", 1)
                        variable_counters[prefix] += 1
```

---

## H. Save Output

```python
import os
import pandas as pd

def save_output(merged_results, template_headers, output_dir):
    output_file = os.path.join(output_dir, "TSRU_Generated_TestPlan.xlsx")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, rows in merged_results.items():
            if rows:
                df = pd.DataFrame(rows)
            else:
                # Preserve headers for empty sheets
                columns = template_headers.get(sheet_name, [])
                df = pd.DataFrame(columns=columns)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
```

---

## Complete Pipeline Summary

```python
def convert_test_plan_to_tsru(template_path, user_plan_path, pinmap_path, output_dir):
    # A. Read inputs
    template_data, template_headers = read_template(template_path)
    pinmap_xml = read_pinmap_groups(pinmap_path)
    user_records = read_user_plan(user_plan_path)

    # B. Group
    chunks = group_test_cases(user_records, pinmap_xml)

    enriched_chunks = []
    for chunk in chunks:
        expanded  = expand_test_cases(chunk, pinmap_xml)        # C
        with_names = enrich_test_name_base(expanded)             # D
        with_groups = enrich_pin_groups(with_names, pinmap_xml)  # E
        enriched_chunks.append(with_groups)

    # F. Map
    merged = map_to_tsru(enriched_chunks, template_data, template_headers)

    # G. Post-process
    post_process(merged, enriched_chunks)

    # H. Save
    save_output(merged, template_headers, output_dir)

    # I. Deploy & generate sequence
    deploy_and_generate(output_dir, tsru_modules_dir="TSRU Modules")
```

---

## I. Deploy to TSRU Modules & Run Generate Seq

```python
import shutil
import subprocess

def deploy_and_generate(output_dir, tsru_modules_dir):
    """
    Copy the generated TSRU Excel into the TSRU Modules folder
    as 'TestSpreadsheet.xlsx', then run 'Generate Seq.cmd'.
    """
    src = os.path.join(output_dir, "TSRU_Generated_TestPlan.xlsx")
    dst = os.path.join(tsru_modules_dir, "TestSpreadsheet.xlsx")

    # Copy & rename
    shutil.copy2(src, dst)

    # Run the sequence generator
    cmd_path = os.path.join(tsru_modules_dir, "Generate Seq.cmd")
    subprocess.run([cmd_path], cwd=tsru_modules_dir, check=True, shell=True)
```
