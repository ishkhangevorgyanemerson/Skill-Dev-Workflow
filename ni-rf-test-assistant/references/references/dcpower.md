# NI-DCPower — Power Supply / SMU Driver Reference

> **Role**: Supply DC power to the DUT (Device Under Test) and/or measure DUT current consumption. NI-DCPower instruments are Source Measure Units (SMUs) capable of sourcing voltage or current while simultaneously measuring the other. Commonly used for DUT biasing, power sequencing, and current consumption profiling.

---

## 6-Phase State Machine Model

NI-DCPower follows a strict 6-phase lifecycle. **Never call APIs out of phase order.**

```
Phase 1: Session Init     → Open session (once per resource name)
Phase 2: Static Config    → Configure ALL channels (source, timing, triggers, sequences)
Phase 3: Execution Activate → Enable output, then Initiate (per channel)
Phase 4: HW Sync          → WaitForEvent (SOURCE_COMPLETE or SEQUENCE_ENGINE_DONE)
Phase 5: Data Retrieval   → Measure (simple) or Fetch (triggered/sequence)
Phase 6: Safe Teardown    → Abort → Disable output → [Delete sequence] → Close
```

### Phase Summary & Rules

| Phase | Purpose | Critical Rules |
|---|---|---|
| **1. Session Init** | Allocate hardware handle | `Session()` called **once** per resource name, regardless of channel count |
| **2. Static Config** | Configure all channels | Configure **every** channel before any Phase 3 call. Includes source, measurement, timing, triggers, and sequences. |
| **3. Execution Activate** | Start hardware | `output_enabled = True` first, then `initiate()`. For multi-channel: initiate each channel. |
| **4. HW Sync** | Block until hardware ready | `wait_for_event(SOURCE_COMPLETE)` for single-point; `wait_for_event(SEQUENCE_ENGINE_DONE)` for sequences. |
| **5. Data Retrieval** | Read measurements | Use `measure()` for simple path; use `fetch_multiple()` for triggered/sequence path. See Measure vs Fetch rule below. |
| **6. Safe Teardown** | Release hardware safely | Strict order: Abort → Disable output → Delete sequence (if used) → Close |

---

## Measure vs Fetch — Critical Distinction

| Method | Use When | Behavior |
|---|---|---|
| `measure()` | **Simple path** — single-point, no triggers, no sequence | Synchronous blocking call. Returns samples directly. Only valid when `initiate()` has NOT been called. |
| `fetch_multiple()` | **Triggered / sequence path** — any test that calls `initiate()` | Synchronous blocking call. Requires explicit `timeout` and `count` parameters. Pulls data from instrument buffer. |

> ⚠️ **Red-line rule**: Once **any** channel on the session calls `initiate()`, **all** data retrieval for that session **must** use `fetch_multiple()`. Never mix `measure()` and `fetch_multiple()` on the same session after initiation.

---

## Aperture Time Default

> 💡 **Expert default**: If the user does not explicitly specify aperture time, always default to **1 PLC** (Power Line Cycle) for optimal power-line noise rejection.
>
> - 1 PLC = 20 ms at 50 Hz mains, 16.67 ms at 60 Hz mains
> - For speed-critical tests, the user may override to a shorter time in seconds

```python
# Default: 1 PLC for best noise rejection
channel.aperture_time = 1
channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES
```

---

## Python API — Single Channel (Simple Path)

```python
import nidcpower

# === Phase 1: Session Init ===
dcpower_session = nidcpower.Session(resource_name="PXI1Slot3")

# === Phase 2: Static Config ===
channel = dcpower_session.channels["0"]

# Configure output function — voltage source with current limit
channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
channel.voltage_level = voltage_level              # V, e.g., 3.3
channel.current_limit = current_limit              # A, e.g., 0.5
channel.current_limit_range = current_limit_range  # A, e.g., 1.0
channel.voltage_level_range = voltage_level_range  # V, e.g., 6.0

# Configure source delay (settling time before measurement)
channel.source_delay = source_delay  # seconds, e.g., 0.01 (10 ms)

# Source mode: single-point (hold one level)
channel.source_mode = nidcpower.SourceMode.SINGLE_POINT

# Configure measurement timing — default 1 PLC for noise rejection
channel.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
channel.aperture_time = 1
channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES

# === Phase 3: Execution Activate ===
channel.output_enabled = True
dcpower_session.initiate()

# === Phase 4: HW Sync ===
channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)

# === Phase 5: Data Retrieval ===
# Using fetch_multiple because initiate() was called
measurements = channel.fetch_multiple(count=1, timeout=10.0)
current = measurements[0].current
logging.info(f"DUT current: {current:.6f} A")

# === Phase 6: Safe Teardown ===
dcpower_session.abort()
channel.output_enabled = False
dcpower_session.close()
```

## C# API — Single Channel (Simple Path)

```csharp
using NationalInstruments.ModularInstruments.NIDCPower;

// === Phase 1: Session Init ===
NIDCPower dcpowerSession = new NIDCPower("PXI1Slot3", "", true);

// === Phase 2: Static Config ===
var channel = dcpowerSession.Outputs["0"];
channel.Source.Output.Function = DCPowerSourceOutputFunction.DCVoltage;
channel.Source.Voltage.VoltageLevel = voltageLevel;
channel.Source.Voltage.CurrentLimit = currentLimit;
channel.Source.SourceDelay = TimeSpan.FromMilliseconds(10);
channel.Measurement.MeasureWhen = DCPowerMeasurementMeasureWhen.AutomaticallyAfterSourceComplete;
channel.Measurement.ApertureTime = 1;
channel.Measurement.ApertureTimeUnits = DCPowerMeasurementApertureTimeUnits.PowerLineCycles;

// === Phase 3: Execution Activate ===
channel.Source.Output.Enabled = true;
dcpowerSession.Control.Initiate();

// === Phase 4: HW Sync ===
channel.Events.SourceCompleteEvent.WaitForEvent(TimeSpan.FromSeconds(10));

// === Phase 5: Data Retrieval ===
DCPowerFetchResult result = channel.Measurement.FetchMultiple(TimeSpan.FromSeconds(10), 1);

// === Phase 6: Safe Teardown ===
dcpowerSession.Control.Abort();
channel.Source.Output.Enabled = false;
dcpowerSession.Close();
```

---

## Configuration Details

### Output Functions

| Function | Enum Value | Description |
|---|---|---|
| DC Voltage | `DC_VOLTAGE` | Source voltage, limit current (most common for DUT biasing) |
| DC Current | `DC_CURRENT` | Source current, limit voltage (battery simulation) |

### Pure Measurement Channel (Zero-Output Active State)

When a channel should only **measure** (not source), it must still be explicitly configured. Set it as a current source at 0 A with a voltage limit matching the expected measurement range:

```python
# Channel 2: measure DUT voltage only (do not source)
measure_channel = dcpower_session.channels["2"]
measure_channel.output_function = nidcpower.OutputFunction.DC_CURRENT
measure_channel.current_level = 0.0           # Source 0 A — no current injection
measure_channel.voltage_limit = 5.0           # Expect up to 5V from DUT
measure_channel.voltage_limit_range = 6.0
measure_channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
measure_channel.aperture_time = 1
measure_channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES
```

> ⚠️ **Every channel that participates in the test must be configured in Phase 2**, even measurement-only channels. Unconfigured channels will use hardware defaults, which may be incorrect or unsafe.

### Source Modes

| Mode | Description | Use Case |
|---|---|---|
| **Single Point** | One voltage/current level, held steady | DUT biasing (most common) |
| **Sequence** | Step through a list of voltage/current levels | Power sweep, IV curve |

### Sequence Mode

For power sweep or characterization across multiple voltage/current points.

> ⚠️ **Sequence path always uses `fetch_multiple()`** — never `measure()`.

```python
# === Phase 2: Configure sequence ===
channel.source_mode = nidcpower.SourceMode.SEQUENCE

voltage_levels = [1.0, 1.5, 2.0, 2.5, 3.0, 3.3]
current_limits = [0.5] * len(voltage_levels)
source_delays = [0.01] * len(voltage_levels)

channel.set_sequence(
    voltage_levels=voltage_levels,
    current_limits=current_limits,
    source_delays=source_delays)

# Configure timing for the sequence
channel.aperture_time = 1
channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES
channel.measure_record_length = len(voltage_levels)

# === Phase 3: Execution Activate ===
channel.output_enabled = True
dcpower_session.initiate()

# === Phase 4: HW Sync — wait for entire sequence to complete ===
channel.wait_for_event(event_id=nidcpower.Event.SEQUENCE_ENGINE_DONE, timeout=30.0)

# === Phase 5: Data Retrieval — MUST use fetch_multiple for sequence path ===
measurements = channel.fetch_multiple(count=len(voltage_levels), timeout=10.0)
for i, m in enumerate(measurements):
    logging.info(f"Step {i}: V={m.voltage:.3f}V, I={m.current:.6f}A")

# === Phase 6: Safe Teardown — delete sequence after abort ===
dcpower_session.abort()
channel.output_enabled = False
channel.delete_advanced_sequence()  # Required when sequence was configured
dcpower_session.close()
```

### Source Delay and Settling

- **Source delay** is the time the SMU waits after changing the output level before taking a measurement. This allows the DUT and output to settle.
- Typical values: 1–100 ms depending on DUT power supply decoupling and load capacitance.
- For RF DUTs with large bypass capacitors, use longer delays (50–100 ms).

### Measurement Timing Configuration

| Parameter | Description | Default / Typical |
|---|---|---|
| `aperture_time` | Integration time for measurement | **1 PLC** (expert default) |
| `aperture_time_units` | Units for aperture time | `POWER_LINE_CYCLES` (default) or `SECONDS` |
| `measure_when` | When to auto-measure | `AUTOMATICALLY_AFTER_SOURCE_COMPLETE` |
| `measure_record_length` | Number of samples per channel (for sequences) | Equal to sequence length |

### Trigger Configuration

For synchronized power-on with other instruments:

```python
# Export source complete event to PXI trigger line
# (signals other instruments that power is stable)
channel.source_complete_event_output_terminal = "/PXI1Slot3/PXI_Trig1"

# Or: configure start trigger from external source
channel.start_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE
channel.digital_edge_start_trigger_source = "PXI_Trig0"
channel.digital_edge_start_trigger_edge = nidcpower.DigitalEdge.RISING
```

---

## Multi-Channel Operation

Many NI-DCPower instruments support multiple channels (e.g., PXIe-4163 has 4 channels). Each channel is independently configurable.

### Multi-Channel Rules

> ⚠️ **Session rule**: `Session()` is called **once** per resource name, regardless of how many channels are used.
>
> ⚠️ **Configuration rule**: **All** channels must be fully configured in Phase 2 before **any** channel enters Phase 3.
>
> ⚠️ **Initiate rule**: In multi-channel scenarios, `initiate()` must be called for each participating channel. Once any channel is initiated, the entire session switches to the `fetch_multiple()` data path.
>
> ⚠️ **Wait rule**: For multi-channel power-on, `wait_for_event(SOURCE_COMPLETE)` is typically only needed on the **source** channels (not pure measurement channels).

### Python Example — Multi-Channel with Measurement Channel

```python
# === Phase 1: Session Init (once) ===
dcpower_session = nidcpower.Session(resource_name="SMU_4147_C1_S11")

# === Phase 2: Static Config (ALL channels before any Phase 3) ===

# Channel 0: VDD — main supply
vdd_channel = dcpower_session.channels["0"]
vdd_channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
vdd_channel.voltage_level = 3.3
vdd_channel.current_limit = 0.5
vdd_channel.current_limit_range = 1.0
vdd_channel.voltage_level_range = 6.0
vdd_channel.source_delay = 0.05  # 50 ms settling for main rail
vdd_channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
vdd_channel.aperture_time = 1
vdd_channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES

# Channel 1: VDDIO — IO supply
vddio_channel = dcpower_session.channels["1"]
vddio_channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
vddio_channel.voltage_level = 1.8
vddio_channel.current_limit = 0.2
vddio_channel.current_limit_range = 0.5
vddio_channel.voltage_level_range = 6.0
vddio_channel.source_delay = 0.05
vddio_channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
vddio_channel.aperture_time = 1
vddio_channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES

# Channel 2: Measurement only — sense DUT output voltage (zero output)
sense_channel = dcpower_session.channels["2"]
sense_channel.output_function = nidcpower.OutputFunction.DC_CURRENT
sense_channel.current_level = 0.0        # No current injection
sense_channel.voltage_limit = 5.0        # Expect up to 5V
sense_channel.voltage_limit_range = 6.0
sense_channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
sense_channel.aperture_time = 1
sense_channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES

logging.info("All channels configured in Phase 2")

# === Phase 3: Execution Activate ===
# Power-on sequencing: VDD first, then VDDIO, then enable sense channel
vdd_channel.output_enabled = True
dcpower_session.initiate()
vdd_channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)
logging.info("VDD supply stable at 3.3V")

vddio_channel.output_enabled = True
dcpower_session.initiate()
vddio_channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)
logging.info("VDDIO supply stable at 1.8V")

sense_channel.output_enabled = True
dcpower_session.initiate()

# === Phase 5: Data Retrieval — MUST use fetch_multiple (initiate was called) ===
vdd_data = vdd_channel.fetch_multiple(count=1, timeout=10.0)
vddio_data = vddio_channel.fetch_multiple(count=1, timeout=10.0)
sense_data = sense_channel.fetch_multiple(count=1, timeout=10.0)

logging.info(f"VDD current: {vdd_data[0].current:.6f} A")
logging.info(f"VDDIO current: {vddio_data[0].current:.6f} A")
logging.info(f"Sense voltage: {sense_data[0].voltage:.3f} V")
```

---

## Required Parameters Checklist

| Parameter | Type | Required? | Notes |
|---|---|---|---|
| `resource_name` | string | **Yes** | e.g., `"PXI1Slot3"` |
| `channel` | string | **Yes** | e.g., `"0"`, `"0,1"` for multiple |
| `output_function` | enum | **Yes** | `DC_VOLTAGE` or `DC_CURRENT` |
| `voltage_level` | float (V) | **Yes** (voltage mode) | DUT supply voltage |
| `current_limit` | float (A) | **Yes** (voltage mode) | Protection limit |
| `current_level` | float (A) | **Yes** (current mode) | Source current level |
| `voltage_limit` | float (V) | **Yes** (current mode) | Protection limit |
| `source_delay` | float (s) | Recommended | Settling time, e.g., 0.01 |
| `voltage_level_range` | float (V) | Recommended | Instrument range selection |
| `current_limit_range` | float (A) | Recommended | Instrument range selection |
| `aperture_time` | float | Default: **1 PLC** | Override only if speed-critical |
| `aperture_time_units` | enum | Default: `POWER_LINE_CYCLES` | Use `SECONDS` for explicit timing |
| `trigger_export_terminal` | string | For multi-instrument | e.g., `"PXI_Trig1"` |

---

## Error Handling & Safe Teardown Pattern (Phase 6)

Teardown must follow strict ordering. Sequence deletion is required only if a sequence was configured.

```python
dcpower_session = None
use_sequence = False  # Track whether sequence mode was configured
try:
    # === Phase 1: Session Init ===
    dcpower_session = nidcpower.Session(resource_name=resource_name)
    logging.info(f"DCPower session opened: {resource_name}")

    # === Phase 2: Static Config ===
    channel = dcpower_session.channels[channel_name]
    channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    channel.voltage_level = voltage_level
    channel.current_limit = current_limit
    channel.source_delay = source_delay
    channel.source_mode = nidcpower.SourceMode.SINGLE_POINT
    channel.aperture_time = 1
    channel.aperture_time_units = nidcpower.ApertureTimeUnits.POWER_LINE_CYCLES
    logging.info(f"DCPower configured: {voltage_level}V, limit {current_limit}A")

    # === Phase 3: Execution Activate ===
    channel.output_enabled = True
    dcpower_session.initiate()
    logging.info("DCPower output enabled, sourcing voltage")

    # === Phase 4: HW Sync ===
    channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)

    # === Phase 5: Data Retrieval (fetch because initiate was called) ===
    measurements = channel.fetch_multiple(count=1, timeout=10.0)
    current = measurements[0].current
    logging.info(f"DUT current consumption: {current:.6f} A")

except Exception as e:
    logging.error(f"DCPower error on {resource_name}: {e}")
    raise

finally:
    if dcpower_session is not None:
        # === Phase 6: Safe Teardown (strict order) ===
        try:
            # Step 1: Abort all running hardware tasks
            dcpower_session.abort()
            # Step 2: Disable output on ALL channels to protect DUT
            for ch in dcpower_session.channels:
                ch.output_enabled = False
            # Step 3: Delete sequence (only if sequence mode was used)
            if use_sequence:
                channel.delete_advanced_sequence()
        except Exception:
            pass  # Best-effort cleanup
        # Step 4: Close session (once)
        dcpower_session.close()
        logging.info(f"DCPower session closed, output disabled: {resource_name}")
```

---

## Prohibited Anti-Patterns ⛔

These are **hard rules** — violating any of them will cause hardware errors, data corruption, or DUT damage.

### 1. Never disable output while running — Abort first
> ⛔ **FORBIDDEN**: Calling `output_enabled = False` while the session is in the Running state (after `initiate()`, before `abort()`).
>
> ✅ **REQUIRED**: Always call `abort()` first, then `output_enabled = False`.

```python
# ❌ WRONG — disabling output while hardware is running
dcpower_session.initiate()
channel.output_enabled = False          # ⛔ May cause undefined behavior

# ✅ CORRECT — abort stops the hardware engine, then disable output
dcpower_session.abort()
channel.output_enabled = False
dcpower_session.close()
```

### 2. Never mix Measure and Fetch data paths
> ⛔ **FORBIDDEN**: Using `measure()` after any channel has called `initiate()`. Once the session enters the triggered/sequence execution path, all data retrieval must use `fetch_multiple()`.

```python
# ❌ WRONG — measure() after initiate()
dcpower_session.initiate()
channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)
current = channel.measure(measurement_type=nidcpower.MeasurementTypes.CURRENT)  # ⛔ Stale/incorrect data

# ✅ CORRECT — fetch_multiple() after initiate()
dcpower_session.initiate()
channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)
measurements = channel.fetch_multiple(count=1, timeout=10.0)
current = measurements[0].current
```

### 3. Never fetch data without confirming source settling
> ⛔ **FORBIDDEN**: Calling `fetch_multiple()` or `measure()` without first calling `wait_for_event(SOURCE_COMPLETE)` (or `SEQUENCE_ENGINE_DONE` for sequences). Skipping the wait returns measurements taken before the output has settled.

```python
# ❌ WRONG — fetching immediately after initiate, no wait
dcpower_session.initiate()
measurements = channel.fetch_multiple(count=1, timeout=10.0)  # ⛔ Data captured during transient

# ✅ CORRECT — wait for source to settle, then fetch
dcpower_session.initiate()
channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)
measurements = channel.fetch_multiple(count=1, timeout=10.0)
```

---

## Common Pitfalls

1. **Forgetting to disable output in teardown** — Always disable output in the `finally` block (Phase 6, Step 2). Leaving voltage applied can damage the DUT during errors.
2. **Using `measure()` after `initiate()`** — Once any channel is initiated, the session is in the triggered path. All retrieval **must** use `fetch_multiple()`. Using `measure()` will either fail or return stale data.
3. **Configuring channels after `initiate()`** — All channel configuration must complete in Phase 2 before any Phase 3 call. Modifying parameters after initiation requires abort → reconfigure → re-initiate.
4. **Current limit too low** — If the current limit is below the DUT's operating current, the SMU enters compliance (voltage drops). Set current limit with margin above expected consumption.
5. **Source delay too short** — Insufficient settling time leads to inaccurate current measurements. Profile DUT power-on transient to determine the correct delay.
6. **Range mismatch** — Setting `current_limit_range` too low truncates current measurement resolution. Set the range to the smallest value that accommodates the limit.
7. **Power sequencing order** — Many DUTs require specific power-on order (e.g., core supply before IO supply). Document and enforce the sequence in code.
8. **Not waiting for source complete** — Measuring before the source has settled gives incorrect readings. Always use `wait_for_event(SOURCE_COMPLETE)` before fetching.
9. **Forgetting to delete sequence** — If a sequence was configured in Phase 2, `delete_advanced_sequence()` must be called in Phase 6 before `close()`. Omitting this can leak hardware resources.
10. **Multiple `Session()` calls for same resource** — Only one session per resource name. Opening a second session on the same resource will fail or cause conflicts.
11. **Unconfigured measurement-only channels** — Every channel that participates must be explicitly configured in Phase 2. For measurement-only channels, use DC_CURRENT at 0 A with an appropriate voltage limit.
