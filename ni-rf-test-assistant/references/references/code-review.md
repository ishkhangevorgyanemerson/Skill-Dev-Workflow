# Code Review & Quality Rules for RF Test Code

> **Purpose**: Defines mandatory code quality rules that apply to all generated, reviewed, or refactored RF test code. These rules ensure production-quality code that is maintainable, debuggable, and safe for instrument hardware and DUTs.

---

## 1. Comments

### Rule 1.1 — Function-Level Docstrings (Mandatory)

Every test function **must** have a docstring that includes:
- **What** the test measures (e.g., "TX EVM for 802.11ax")
- **Which instruments** are used (e.g., "DCPower, Digital, RFmx WLAN")
- **Key parameters** described (frequency, power, standard)
- **Return value** description

```python
# ✅ GOOD
def test_tx_evm_wlan_ax(center_frequency, reference_level, channel_bandwidth,
                         mcs_index, voltage_level, current_limit):
    """
    Measure TX EVM for an 802.11ax (Wi-Fi 6) signal.

    Instruments:
        - NI-DCPower: Powers the DUT at the specified voltage.
        - NI-Digital: Configures DUT band/channel/TX mode via SPI.
        - NI-RFmx WLAN: Measures OFDM ModAcc (EVM) on the DUT output.

    Args:
        center_frequency: Signal center frequency in Hz (e.g., 5.18e9).
        reference_level: Expected signal power in dBm (e.g., -10.0).
        channel_bandwidth: Channel bandwidth in Hz (e.g., 80e6).
        mcs_index: Modulation and coding scheme index (0-11).
        voltage_level: DUT supply voltage in V (e.g., 3.3).
        current_limit: SMU current limit in A (e.g., 0.5).

    Returns:
        dict: {"composite_rms_evm_db": float, "frequency_error_hz": float}
    """
```

```python
# ❌ BAD — No docstring, or one-liner with no detail
def test_evm(freq, pwr, bw):
    pass
```

### Rule 1.2 — Section Comments (Mandatory)

Each major section of the test function must be marked with a section comment following the standard structure:

```python
# === 1. SETUP — Open sessions ===
# === 2. CONFIGURE — Set instrument parameters ===
# === 3. EXECUTE — Arm triggers, initiate, acquire ===
# === 4. FETCH — Retrieve measurement results ===
# === 5. VERIFY — Compare results against limits ===
# === 6. CLEANUP — Close all sessions in finally block ===
```

### Rule 1.3 — Configuration Comments (Mandatory)

Every configuration block must have an inline or block comment explaining **what** is being configured and **why** the value is chosen:

```python
# ✅ GOOD
# Set reference level 5 dB above expected DUT output power to avoid ADC clipping
rfmx_wlan.set_reference_level(selector_string="", reference_level=reference_level)

# Configure 50 ms source delay to allow DUT power supply to settle
# before measuring quiescent current
channel.source_delay = 0.05

# ❌ BAD — No explanation
rfmx_wlan.set_reference_level(selector_string="", reference_level=-10.0)
channel.source_delay = 0.05
```

### Rule 1.4 — Trigger Wiring Comments (Mandatory for Multi-Instrument)

When triggers connect instruments, add a comment block explaining the trigger flow:

```python
# ✅ GOOD
# Trigger wiring:
#   Digital pattern "enable_tx" completes → exports rising edge on PXI_Trig2
#   RFmx WLAN is armed on PXI_Trig2 (digital edge, rising)
#   Trigger delay: 100 µs to allow DUT TX ramp-up
rfmx_wlan.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig2")
```

---

## 2. Logging

### Rule 2.1 — Use Standard Logging Module

```python
import logging
logger = logging.getLogger(__name__)
```

For C#, use `ILogger` or framework-appropriate logging.

### Rule 2.2 — Mandatory INFO-Level Log Points

The following events **must** be logged at INFO level:

| Event | Example Log Message |
|---|---|
| Session open | `"DCPower session opened: PXI1Slot3"` |
| Session close | `"DCPower session closed: PXI1Slot3"` |
| Key parameter values | `"Configuring: frequency=5.18 GHz, reference_level=-10 dBm, BW=80 MHz"` |
| DUT power on/off | `"DUT powered: 3.3V, current limit 0.5A"` |
| DUT mode configuration | `"DUT configured for TX mode: band=5GHz, channel=36"` |
| Measurement initiate | `"RFmx WLAN OFDM ModAcc measurement initiated"` |
| Measurement result | `"TX EVM result: -35.2 dB (limit: -25 dB) — PASS"` |
| Analyzer trigger armed | `"RFmx analyzer armed, waiting for trigger on PXI_Trig2"` |
| Test pass/fail | `"Test PASSED: all results within limits"` |

### Rule 2.3 — DEBUG-Level Logging (Recommended)

| Event | Example |
|---|---|
| Raw fetch results | `"Raw OFDM ModAcc results: {full_result_dict}"` |
| Trigger state | `"Trigger configured: type=DigitalEdge, source=PXI_Trig2, edge=Rising"` |
| Waveform loaded | `"Waveform 'wifi6_80mhz' loaded: 1000000 samples, IQ rate=200 MS/s"` |
| DUT register values | `"SPI write: addr=0x1A, data=0xFF"` |

### Rule 2.4 — ERROR-Level Logging (Mandatory for Exceptions)

```python
# ✅ GOOD — Descriptive error context
except Exception as e:
    logging.error(f"RFmx WLAN EVM measurement failed on VST1 "
                  f"(freq={center_frequency/1e9:.3f} GHz, BW={channel_bandwidth/1e6:.0f} MHz): {e}")
    raise

# ❌ BAD — No context
except Exception as e:
    logging.error(f"Error: {e}")
    raise
```

---

## 3. Error Handling

### Rule 3.1 — try/finally for All Sessions (Mandatory)

Every instrument session must be opened in a `try` block with cleanup in `finally`:

```python
# ✅ GOOD
dcpower_session = None
rfmx_instr = None
try:
    dcpower_session = nidcpower.Session(resource_name="PXI1Slot3")
    rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name="VST1", option_string="")
    # ... test code ...
finally:
    if rfmx_instr is not None:
        rfmx_instr.close()
    if dcpower_session is not None:
        dcpower_session.channels["0"].output_enabled = False
        dcpower_session.abort()
        dcpower_session.close()
```

```python
# ❌ BAD — No finally block
dcpower_session = nidcpower.Session(resource_name="PXI1Slot3")
# ... test code that might throw ...
dcpower_session.close()  # Never reached if exception occurs
```

### Rule 3.2 — Close in Reverse Order

Sessions must be closed in **reverse order** of initialization:
1. RFmx personality → dispose
2. RFmx instrument → close
3. RFSG → abort, close
4. Digital → close
5. DCPower → disable output, abort, close

### Rule 3.3 — DCPower Output Disable in Finally (Mandatory)

DCPower `output_enabled = False` must **always** be in the `finally` block. A DUT left powered with no software control is a safety/damage risk.

### Rule 3.4 — RFSG Abort Before Close (Mandatory)

Always call `rfsg_session.abort()` before `rfsg_session.close()` to stop active generation.

### Rule 3.5 — C# Dispose Pattern

```csharp
// ✅ GOOD — using statement or explicit Dispose in finally
RFmxSpecAnMX rfmxSpecAn = null;
try
{
    rfmxSpecAn = rfmxInstr.GetSpecAnSignalConfiguration("Signal");
    // ... test code ...
}
finally
{
    rfmxSpecAn?.Dispose();
    rfmxInstr?.Close();
}
```

---

## 4. Naming Conventions

### Rule 4.1 — Language-Appropriate Case

| Language | Convention | Example |
|---|---|---|
| Python | `snake_case` | `center_frequency`, `rfmx_wlan_session` |
| C# | `PascalCase` | `CenterFrequency`, `RfmxWlanSession` |

### Rule 4.2 — Descriptive Variable Names (Mandatory)

Variable names must reflect the instrument, signal, or measurement:

```python
# ✅ GOOD
rfmx_wlan_session = rfmx_instr.get_rfmx_wlan_signal("WLAN_Signal")
dcpower_session = nidcpower.Session(resource_name="PXI1Slot3")
composite_rms_evm_db = rfmx_wlan.ofdm_modacc.results.fetch_composite_rms_evm_mean(...)
dut_current_amps = channel.measure(measurement_type=nidcpower.MeasurementTypes.CURRENT)

# ❌ BAD
s1 = rfmx_instr.get_rfmx_wlan_signal("WLAN_Signal")
sess = nidcpower.Session(resource_name="PXI1Slot3")
result = rfmx_wlan.ofdm_modacc.results.fetch_composite_rms_evm_mean(...)
val = channel.measure(measurement_type=nidcpower.MeasurementTypes.CURRENT)
```

### Rule 4.3 — Test Function Naming

```python
# Pattern: test_<measurement>_<standard>_<variant>
def test_tx_evm_wlan_ax():       # TX EVM for 802.11ax
def test_acp_nr_fr1():            # ACP for 5G NR FR1
def test_rx_per_wlan_n():         # RX PER for 802.11n
def test_tx_power_specan():       # TX power via SpecAn
```

---

## 5. Magic Number Prohibition

### Rule 5.1 — No Inline RF Parameter Literals (Mandatory)

All RF parameters must be function arguments or named constants:

```python
# ✅ GOOD
CENTER_FREQUENCY_HZ = 5.18e9
REFERENCE_LEVEL_DBM = -10.0
CHANNEL_BANDWIDTH_HZ = 80e6

rfmx_wlan.set_frequency(selector_string="", frequency=CENTER_FREQUENCY_HZ)

# ❌ BAD — Magic numbers
rfmx_wlan.set_frequency(selector_string="", frequency=5180000000)
rfmx_wlan.set_reference_level(selector_string="", reference_level=-10)
```

### Rule 5.2 — Allowed Defaults

The following values may be used inline without being named constants:
- Timeout: `10.0` (seconds)
- Selector string: `""`
- External attenuation: `0.0` (when no fixture present)
- Pre-filter gain: `-2.0` (standard OFDM headroom)
- Source delay: documented inline with comment

---

## 6. Code Structure

### Rule 6.1 — Standard Test Function Skeleton

Every test function must follow the 6-section structure:

```python
def test_<measurement>_<standard>(parameters...):
    """Docstring (Rule 1.1)"""
    session_var_1 = None
    session_var_2 = None
    try:
        # === 1. SETUP — Open sessions ===
        # === 2. CONFIGURE — Set instrument parameters ===
        # === 3. EXECUTE — Arm triggers, initiate, acquire ===
        # === 4. FETCH — Retrieve measurement results ===
        # === 5. VERIFY — Compare results against limits (if applicable) ===
        return results
    except Exception as e:
        logging.error(f"Descriptive error message: {e}")
        raise
    finally:
        # === 6. CLEANUP — Close all sessions in finally block ===
```

### Rule 6.2 — Single Responsibility

Each test function performs **one measurement type on one signal standard**. Do not combine WLAN EVM + SpecAn ACP in one function (also required by the RFmx personality exclusion rule).

### Rule 6.3 — Return Results as Dictionary

```python
# ✅ GOOD — Structured return
return {
    "composite_rms_evm_db": composite_rms_evm,
    "frequency_error_hz": frequency_error,
    "pass": composite_rms_evm < evm_limit
}

# ❌ BAD — Print-only, no return
print(f"EVM = {composite_rms_evm}")
```

---

## 7. Review Checklist

When reviewing existing code, check each item and report findings with severity:

| # | Check | Severity |
|---|---|---|
| 1 | All sessions closed in `finally` block | 🔴 Critical |
| 2 | DCPower output disabled in `finally` | 🔴 Critical |
| 3 | No magic numbers for RF parameters | 🔴 Critical |
| 4 | Correct API usage per driver reference file | 🔴 Critical |
| 5 | try/finally wraps all instrument code | 🔴 Critical |
| 6 | RFSG abort before close | 🟡 Warning |
| 7 | Function docstring present and complete | 🟡 Warning |
| 8 | Section comments present | 🟡 Warning |
| 9 | Logging at INFO level for key events | 🟡 Warning |
| 10 | Descriptive variable names | 🟡 Warning |
| 11 | Error messages include context | 🟡 Warning |
| 12 | Trigger wiring documented in comments | 🟡 Warning (multi-instrument) |
| 13 | Configuration comments explain *why* | 🟢 Suggestion |
| 14 | DEBUG logging for raw results | 🟢 Suggestion |
| 15 | Results returned as dict | 🟢 Suggestion |
| 16 | Test function follows naming convention | 🟢 Suggestion |

### Review Report Format

When reviewing code, present findings as:

```
## Code Review Results

### 🔴 Critical Issues
1. [Line X] DCPower output not disabled in finally block — DUT may remain powered on error.
   **Fix**: Add `channel.output_enabled = False` in finally block.

### 🟡 Warnings
2. [Line Y] Missing section comments — code structure is unclear.
   **Fix**: Add `# === 1. SETUP ===`, etc.

### 🟢 Suggestions
3. [Line Z] Variable `s` should be renamed to `rfmx_wlan_session` for clarity.
```
