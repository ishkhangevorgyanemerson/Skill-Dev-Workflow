# NI-Digital — Digital Pattern Instrument Driver Reference

> **Role**: Control DUT registers and communication buses via digital pattern sequences. Used for SPI, I2C, and RFFE (MIPI) protocol communication to configure DUT operating mode, band, channel, gain, and other register settings during RF tests.
---

## Two Operating Modes (Mutually Exclusive)

| Mode | Purpose | Key APIs |
|---|---|---|
| **Pattern** | Load & execute pre-compiled `.digipat` vector files for digital functional test | `load_pattern`, `burst_pattern`, `fetch_capture_waveform` |
| **PPMU** | Force constant voltage or current on specified pins for DC parametric measurement | `ppmu_output_function`, `ppmu_voltage_level`, `ppmu_current_limit` |

> **Hard Rule**: The same pin can only operate in one mode at a time. Switching modes requires completing cleanup of the current mode first.

---

## Core State Machine (Mandatory Sequence)

Generated code **must** follow these paths strictly. Skipping or reordering steps is prohibited.

### Phase 1 — Initialization & Configuration (must execute first)

```
Initialize → LoadPinMap → LoadSpecifications → LoadTiming → LoadLevels → ApplyLevelsAndTiming
```

### Phase 2a — Synchronous Pattern Burst (blocking)

```
LoadPattern → BurstPattern(wait_until_done=True)
```

### Phase 2b — Asynchronous Pattern Burst (non-blocking)

```
LoadPattern → BurstPattern(wait_until_done=False) → [perform other non-HW work] → WaitUntilDone
```

### Phase 2c — Source Waveform Execution (data must be written before burst)

```
LoadPattern → WriteSequenceRegister → CreateSourceWaveform → WriteSourceWaveform → BurstPattern
```

### Phase 2d — PPMU Mode (independent path, mutually exclusive with Pattern)

```python
# Force voltage, measure current
pin.ppmu_output_function = nidigital.PPMUOutputFunction.VOLTAGE
pin.ppmu_voltage_level = 1.8          # V
pin.ppmu_current_limit_range = 0.032  # A
pin.ppmu_source()
current = pin.ppmu_measure(nidigital.PPMUMeasurementType.CURRENT)
pin.ppmu_source()  # call again or reconfigure before switching back

# Force current, measure voltage
pin.ppmu_output_function = nidigital.PPMUOutputFunction.CURRENT
pin.ppmu_current_level = 0.001        # A
pin.ppmu_voltage_limit_high = 3.6     # V
pin.ppmu_voltage_limit_low = 0.0      # V
pin.ppmu_source()
voltage = pin.ppmu_measure(nidigital.PPMUMeasurementType.VOLTAGE)
```

### Phase 3 — Cleanup (must execute before Close)

```
UnloadAllPatterns → Close
```

### Python API — Full Lifecycle (follows state machine)

```python
import nidigital
import logging

# ── Phase 1: Initialize & Configure ──────────────────────────
digital_session = nidigital.Session(resource_name="PXI1Slot5")

digital_session.load_pin_map(pin_map_file_path=pin_map_file)

# Load specifications, levels, and timing from project files
digital_session.load_specifications_levels_and_timing(
    specifications_file_paths=specifications_file,
    levels_file_paths=levels_file,
    timing_file_paths=timing_file)

digital_session.apply_levels_and_timing(
    levels_sheet="default_levels",
    timing_sheet="default_timing")

# ── Phase 2a: Synchronous burst ──────────────────────────────
digital_session.load_pattern(file_path=pattern_file)

digital_session.burst_pattern(
    start_label="spi_write_register",
    select_digital_function=True,
    wait_until_done=True,       # blocking — returns after pattern completes
    timeout=10.0)

# ── Phase 2b: Asynchronous burst (alternative) ──────────────
digital_session.burst_pattern(
    start_label="long_running_pattern",
    select_digital_function=True,
    wait_until_done=False,      # non-blocking — returns immediately
    timeout=10.0)
# ... perform other non-hardware work here ...
digital_session.wait_until_done(timeout=10.0)   # block until pattern finishes

# ── Phase 2c: Source waveform execution ──────────────────────
digital_session.load_pattern(file_path=source_pattern_file)
digital_session.create_source_waveform_from_file_tdms(
    waveform_name="tx_data",
    waveform_file_path=tdms_file)
# OR: write programmatically
digital_session.write_source_waveform_site_unique(
    waveform_name="tx_data",
    waveform_data={0: data_array})
digital_session.burst_pattern(
    start_label="source_pattern",
    select_digital_function=True,
    wait_until_done=True,
    timeout=10.0)

# ── Capture results (for read operations) ────────────────────
capture_waveform = digital_session.fetch_capture_waveform(
    site_list="site0",
    waveform_name="read_data",
    samples_to_read=8,
    timeout=10.0)

# ── Phase 3: Cleanup ─────────────────────────────────────────
digital_session.unload_all_patterns()   # free instrument memory
digital_session.close()
```

### C# API

```csharp
using NationalInstruments.ModularInstruments.NIDigital;

// ── Phase 1: Initialize & Configure ──────────────────────────
NIDigital digitalSession = new NIDigital("PXI1Slot5", false, false, "");
digitalSession.LoadPinMap(pinMapFilePath);
digitalSession.LoadSpecificationsLevelsAndTiming(
    specificationsFilePaths, levelsFilePaths, timingFilePaths);
digitalSession.ApplyLevelsAndTiming("default_levels", "default_timing");

// ── Phase 2a: Synchronous burst ──────────────────────────────
digitalSession.LoadPattern(patternFilePath);
digitalSession.PatternControl.BurstPattern(
    "", "spi_write_register", true, true, TimeSpan.FromSeconds(10));

// ── Phase 2b: Asynchronous burst ─────────────────────────────
digitalSession.PatternControl.BurstPattern(
    "", "long_running_pattern", true, false, TimeSpan.FromSeconds(10));
// ... other non-hardware work ...
digitalSession.PatternControl.WaitUntilDone(TimeSpan.FromSeconds(10));

// ── Fetch capture ────────────────────────────────────────────
uint[,] captureData = digitalSession.PatternResults.FetchCaptureWaveform(
    "site0", "read_data", 8, TimeSpan.FromSeconds(10));

// ── Phase 3: Cleanup ─────────────────────────────────────────
digitalSession.PatternControl.UnloadAllPatterns();
digitalSession.Close();
```

---

## Trigger Configuration

### Exporting a Trigger from a Pattern Opcode Event (DUT start command → other instruments)

```python
# Export Pattern Opcode Event 0 to a PXI trigger line
# Use this when an opcode inside the .digipat marks the exact DUT TX-enable point
digital_session.exported_patterns.pattern_opcode_event0.output_terminal = "/PXI1Slot5/PXI_Trig0"
```

```c
/* C API equivalent: export Pattern Opcode Event 0 on PXI_Trig0 */
niDigital_ExportSignal(
    vi,
    NIDIGITAL_VAL_PATTERN_OPCODE_EVENT,
    "patternOpcodeEvent0",
    "PXI_Trig0");
```

**Rule**: When the digital pattern contains an opcode event at the DUT TX-enable or switch-on vector, prefer exporting that **Pattern Opcode Event** as the hardware trigger. This is normally the best trigger source for synchronizing RFmx or other PXI instruments because it is tied to the exact vector location in the pattern.

Available export points:

| Opcode Event | Python Property | C API Signal Identifier | Typical Use |
|---|---|---|---|
| Event 0 | `exported_patterns.pattern_opcode_event0.output_terminal` | `"patternOpcodeEvent0"` | Primary DUT TX-enable trigger |
| Event 1 | `exported_patterns.pattern_opcode_event1.output_terminal` | `"patternOpcodeEvent1"` | Secondary timing marker |
| Event 2 | `exported_patterns.pattern_opcode_event2.output_terminal` | `"patternOpcodeEvent2"` | User-defined marker |
| Event 3 | `exported_patterns.pattern_opcode_event3.output_terminal` | `"patternOpcodeEvent3"` | User-defined marker |

> **Prefer this over a generic software or delayed trigger** when the `.digipat` already includes the opcode event at the timing point of interest.

### Importing a Trigger (waiting for external event)

```python
# Wait for external trigger before bursting pattern
digital_session.start_trigger_type = nidigital.TriggerType.DIGITAL_EDGE
digital_session.digital_edge_start_trigger_source = "PXI_Trig0"
digital_session.digital_edge_start_trigger_edge = nidigital.DigitalEdge.RISING
```

### Pattern-Internal Conditional Wait

Patterns can include `wait` or `jump` instructions that pause execution until a hardware trigger arrives, enabling tight synchronization within a pattern sequence.

---

## File Dependencies

NI-Digital requires several external files that define the test system:

| File Type | Extension | Purpose |
|---|---|---|
| **Project** | `.digiproj` | Master project file — contains references to **all** files below |
| **Pin Map** | `.pinmap` | Maps logical pin names to physical instrument channels |
| **Specifications** | `.specs` | Defines named level/timing values |
| **Levels** | `.digilevels` | Pin-level voltage definitions (VIL, VIH, VOL, VOH) |
| **Timing** | `.digitiming` | Clock edge placement, strobe timing |
| **Pattern** | `.digipat` | Digital vector pattern (stimulus + expected response) |

These files are typically created in NI Digital Pattern Editor and referenced by path in code.

### Resolving File Paths from `.digiproj`

Sometimes the user provides **only** the `.digiproj` project path instead of individual file paths. The `.digiproj` file is an XML file that contains relative paths to all pin map, specifications, levels, timing, and pattern files used by the project.

**Rule**: When the user provides a `.digiproj` path, parse it to extract the referenced file paths before generating code.

```python
import xml.etree.ElementTree as ET
import os

def resolve_digital_project_files(digiproj_path: str) -> dict:
    """
    Parse a .digiproj file and return resolved absolute paths
    for all referenced digital pattern project files.
    """
    project_dir = os.path.dirname(os.path.abspath(digiproj_path))
    tree = ET.parse(digiproj_path)
    root = tree.getroot()

    # Common XML namespace used by NI Digital projects
    ns = {'dp': root.tag.split('}')[0].strip('{') if '}' in root.tag else ''}

    files = {
        'pin_map': [],        # .pinmap
        'specifications': [], # .specs
        'levels': [],         # .digilevels
        'timing': [],         # .digitiming
        'patterns': [],       # .digipat
    }

    extension_map = {
        '.pinmap': 'pin_map',
        '.specs': 'specifications',
        '.digilevels': 'levels',
        '.digitiming': 'timing',
        '.digipat': 'patterns',
    }

    # Walk all elements looking for file references
    for elem in root.iter():
        # Check attributes and text for file paths
        for value in list(elem.attrib.values()) + ([elem.text] if elem.text else []):
            if not isinstance(value, str):
                continue
            for ext, category in extension_map.items():
                if value.lower().endswith(ext):
                    abs_path = os.path.normpath(os.path.join(project_dir, value))
                    if abs_path not in files[category]:
                        files[category].append(abs_path)

    logging.info(f"Resolved from {digiproj_path}: "
                 f"{len(files['pin_map'])} pin map(s), "
                 f"{len(files['specifications'])} spec(s), "
                 f"{len(files['levels'])} level(s), "
                 f"{len(files['timing'])} timing(s), "
                 f"{len(files['patterns'])} pattern(s)")
    return files
```

**Usage in test code**:
```python
# User provides only: digiproj_path = r"C:\Projects\MyDUT\MyDUT.digiproj"
project_files = resolve_digital_project_files(digiproj_path)

digital_session.load_pin_map(pin_map_file_path=project_files['pin_map'][0])
digital_session.load_specifications_levels_and_timing(
    specifications_file_paths=project_files['specifications'],
    levels_file_paths=project_files['levels'],
    timing_file_paths=project_files['timing'])
digital_session.apply_levels_and_timing(
    levels_sheet="default_levels",
    timing_sheet="default_timing")
for pat in project_files['patterns']:
    digital_session.load_pattern(file_path=pat)
```

---

## Required Parameters Checklist

| Parameter | Type | Required? | Notes |
|---|---|---|---|
| `resource_name` | string | **Yes** | e.g., `"PXI1Slot5"` |
| `digiproj_path` | file path | **Alt** | `.digiproj` — if provided, extract all file paths below from it |
| `pin_map_file` | file path | **Yes***| `.pinmap` file |
| `specifications_file` | file path | **Yes***| `.specs` file |
| `levels_file` | file path | **Yes***| `.digilevels` file |
| `timing_file` | file path | **Yes***| `.digitiming` file |
| `pattern_file` | file path | **Yes***| `.digipat` file (one or more) |
| `start_label` | string | **Yes†** | Required when the test calls `burst_pattern(...)` |
| `levels_sheet` | string | **Yes** | Sheet name from levels file |
| `timing_sheet` | string | **Yes** | Sheet name from timing file |
| `trigger_export_terminal` | string | For multi-instrument | e.g., `"PXI_Trig2"` |

> ***Yes***: Required when `digiproj_path` is not provided. If `digiproj_path` is given, these are auto-resolved from the project file.

> **† Yes**: Required when the test needs to burst a digital pattern. Use the label defined inside the loaded pattern file, for example `spi_write_register` or `source_pattern`.

---

## Error Handling Pattern

```python
digital_session = None
try:
    # ── Phase 1: Initialize & Configure ──────────────────────
    digital_session = nidigital.Session(resource_name=resource_name)
    logging.info(f"Digital session opened: {resource_name}")

    digital_session.load_pin_map(pin_map_file_path=pin_map_file)
    digital_session.load_specifications_levels_and_timing(
        specifications_file_paths=specifications_file,
        levels_file_paths=levels_file,
        timing_file_paths=timing_file)
    digital_session.apply_levels_and_timing(
        levels_sheet=levels_sheet, timing_sheet=timing_sheet)
    digital_session.load_pattern(file_path=pattern_file)
    logging.info("Digital pattern files loaded successfully")

    # ── Phase 2: Burst pattern ───────────────────────────────
    digital_session.burst_pattern(
        start_label=pattern_label,
        select_digital_function=True,
        wait_until_done=True,
        timeout=timeout)
    logging.info(f"Digital pattern '{pattern_label}' executed successfully")

    # Check for failures
    pass_fail = digital_session.get_fail_count()
    if any(count > 0 for count in pass_fail.values()):
        logging.warning(f"Digital pattern failures detected: {pass_fail}")

except Exception as e:
    logging.error(f"Digital pattern error on {resource_name}: {e}")
    raise

finally:
    # ── Phase 3: Cleanup ─────────────────────────────────────
    if digital_session is not None:
        digital_session.unload_all_patterns()   # free instrument memory first
        digital_session.close()
        logging.info(f"Digital session closed: {resource_name}")
```

---

## Prohibited Anti-Patterns ⛔

### 1. Never `BurstPattern` before `LoadPattern`

Pattern must be loaded into instrument memory before execution.

```python
# ❌ WRONG — pattern not loaded yet
digital_session.burst_pattern(start_label="spi_write", ...)

# ✅ CORRECT
digital_session.load_pattern(file_path=pattern_file)
digital_session.burst_pattern(start_label="spi_write", ...)
```

### 2. Never mix PPMU and Pattern mode on the same pin simultaneously

The two modes are mutually exclusive. Complete and clean up the current mode before switching.

```python
# ❌ WRONG — pin is still in PPMU source mode
pin.ppmu_source()
digital_session.burst_pattern(start_label="spi_write", ...)  # conflicts with PPMU

# ✅ CORRECT — disable PPMU before switching to Pattern
pin.ppmu_source()       # finish PPMU measurement
current = pin.ppmu_measure(nidigital.PPMUMeasurementType.CURRENT)
# ... then later, in a separate step ...
digital_session.burst_pattern(
    start_label="spi_write",
    select_digital_function=True,   # switches pin back to digital mode
    wait_until_done=True, timeout=10.0)
```

### 3. Never call any API before `Initialize` (Session constructor)

`Initialize` is the prerequisite for every operation. The session object must exist.

### 4. Never `BurstPattern` before `WriteSourceWaveform` for source-waveform patterns

`WriteSourceWaveform` must complete before `BurstPattern`; otherwise the instrument plays empty data.

```python
# ❌ WRONG — data written after burst
digital_session.load_pattern(file_path=source_pattern_file)
digital_session.burst_pattern(start_label="source_test", ...)
digital_session.write_source_waveform_site_unique(...)   # too late

# ✅ CORRECT — data written before burst
digital_session.load_pattern(file_path=source_pattern_file)
digital_session.create_source_waveform_from_file_tdms(...)
digital_session.write_source_waveform_site_unique(...)    # data ready
digital_session.burst_pattern(start_label="source_test", ...)
```

### 5. Never skip `UnloadAllPatterns` before `Close`

Omitting unload leaks instrument memory and may cause failures in subsequent test sessions.

```python
# ❌ WRONG — patterns still in instrument memory
digital_session.close()

# ✅ CORRECT
digital_session.unload_all_patterns()
digital_session.close()
```

---

## Common Pitfalls

1. **Pin map mismatch** — The pin map must exactly match the physical wiring. A wrong mapping sends data to wrong DUT pins.
2. **Logic level mismatch** — Setting VIH to 3.3V when the DUT uses 1.8V logic can damage the DUT. Always confirm logic family voltage.
3. **Timing violations** — SPI/I2C/RFFE have minimum setup/hold time requirements. Ensure the timing sheet meets the DUT's datasheet specs.
4. **Missing pattern files** — All patterns referenced by `burst_pattern(start_label=...)` must be pre-loaded. Load order matters if patterns reference sub-patterns.
5. **Bidirectional pin mode** — For I2C SDA and RFFE SDATA, the pin must switch between drive and compare within the pattern. Verify the pattern file handles this correctly.
6. **Pattern failure handling** — Always check `get_fail_count()` after bursting. A failed pattern means the DUT did not respond as expected (could indicate misconfiguration, DUT fault, or timing issue).
7. **Async burst without WaitUntilDone** — If `wait_until_done=False`, you **must** call `wait_until_done()` before accessing results or closing the session.
8. **PPMU mode not cleaned up** — Leaving a pin in PPMU source mode and then attempting Pattern mode will fail or produce wrong results.
