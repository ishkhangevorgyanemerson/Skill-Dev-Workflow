# Multi-Instrument Orchestration — Trigger, Sync & Execution Order

> **Purpose**: This document describes how NI instruments work together in a multi-instrument RF test. It covers execution order, trigger wiring conventions, synchronization patterns, and common multi-instrument test architectures.

---

## Instruments in a Typical RF Test System

| Instrument | Role | Session Type |
|---|---|---|
| **NI-DCPower (SMU)** | Power the DUT | `nidcpower.Session` |
| **NI-Digital** | Control DUT registers via SPI/I2C/RFFE | `nidigital.Session` |
| **NI-RFSG** | Generate RF signals (source, interferer, loopback) | `nirfsg.Session` |
| **NI-RFmx** (SpecAn/WLAN/NR) | Analyze DUT RF output | `RFmxInstrMX` + personality |

---

## Test Architecture: TX Test (DUT Transmits)

In a TX test, the DUT generates an RF signal that the analyzer measures. The most common RF production test.

### Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: DCPower — Power ON the DUT                             │
│          Configure voltage, current limit, enable output         │
│          Wait for source complete (power settled)                │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Digital — Configure DUT mode                           │
│          SPI/I2C/RFFE write: set band, channel, TX gain, mode   │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: RFmx — Configure analyzer                              │
│          Set frequency, reference level, standard, measurement   │
│          Configure trigger (digital edge on PXI_Trig line)      │
│          Initiate measurement (analyzer is now armed, waiting)   │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Digital — Command DUT to transmit                      │
│          SPI/RFFE write: enable TX, set power level              │
│          Export trigger on PXI line → triggers analyzer           │
│          (Or: DUT self-starts TX after register write)           │
├─────────────────────────────────────────────────────────────────┤
│  Step 5: RFmx — Acquire and fetch results                       │
│          Analyzer triggered, acquires signal, processes          │
│          Fetch EVM, power, SEM, etc.                            │
├─────────────────────────────────────────────────────────────────┤
│  Step 6: Digital — Command DUT to stop TX                       │
│          SPI/RFFE write: disable TX                              │
├─────────────────────────────────────────────────────────────────┤
│  Step 7: DCPower — Power OFF the DUT (in finally block)         │
│          Disable output, close session                           │
└─────────────────────────────────────────────────────────────────┘
```

### Python Code Skeleton (TX Test)

```python
def test_tx_evm(center_frequency, reference_level, standard, channel_bandwidth,
                mcs_index, voltage_level, current_limit, resource_names, trigger_line):
    """
    TX EVM test: Power DUT, configure via SPI, measure TX EVM with RFmx.

    Instruments: DCPower (SMU), Digital (DUT control), RFmx WLAN (analyzer)
    Trigger: Digital exports on trigger_line after TX enable command.
    """
    dcpower_session = None
    digital_session = None
    rfmx_instr = None
    rfmx_wlan = None

    try:
        # === Step 1: Power ON DUT ===
        dcpower_session = nidcpower.Session(resource_name=resource_names["dcpower"])
        channel = dcpower_session.channels["0"]
        channel.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        channel.voltage_level = voltage_level
        channel.current_limit = current_limit
        channel.source_delay = 0.05  # 50 ms settling
        channel.output_enabled = True
        dcpower_session.initiate()
        channel.wait_for_event(event_id=nidcpower.Event.SOURCE_COMPLETE, timeout=10.0)
        logging.info(f"DUT powered: {voltage_level}V")

        # === Step 2: Configure DUT via Digital ===
        digital_session = nidigital.Session(resource_name=resource_names["digital"])
        digital_session.load_pin_map(pin_map_file_path=pin_map_file)
        # ... load specs, timing, patterns ...
        digital_session.burst_pattern(start_label="configure_dut_tx_mode",
                                       select_digital_function=True,
                                       wait_until_done=True, timeout=10.0)
        logging.info("DUT configured for TX mode")

        # === Step 3: Configure RFmx Analyzer (armed, waiting for trigger) ===
        rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name=resource_names["analyzer"],
                                                option_string="")
        rfmx_wlan = rfmx_instr.get_rfmx_wlan_signal("WLAN_Signal")
        rfmx_wlan.set_frequency(selector_string="", frequency=center_frequency)
        rfmx_wlan.set_reference_level(selector_string="", reference_level=reference_level)
        rfmx_wlan.set_standard(selector_string="", standard=standard)
        rfmx_wlan.set_channel_bandwidth(selector_string="", channel_bandwidth=channel_bandwidth)
        # Configure trigger — wait for DUT TX start
        rfmx_wlan.set_trigger_type(selector_string="",
                                     trigger_type=niRFmxWLAN.TriggerType.DIGITAL_EDGE)
        rfmx_wlan.set_digital_edge_trigger_source(selector_string="", source=trigger_line)
        rfmx_wlan.select_measurements(selector_string="",
                                        measurements=niRFmxWLAN.MeasurementTypes.OFDM_MODACC,
                                        enable_all_traces=True)
        rfmx_wlan.initiate(selector_string="", result_name="")
        logging.info("RFmx WLAN analyzer armed, waiting for trigger")

        # === Step 4: Command DUT to transmit ===
        digital_session.burst_pattern(start_label="enable_dut_tx",
                                       select_digital_function=True,
                                       wait_until_done=True, timeout=10.0)
        logging.info("DUT TX enabled — signal should be transmitting")

        # === Step 5: Fetch measurement results ===
        composite_rms_evm = rfmx_wlan.ofdm_modacc.results.fetch_composite_rms_evm_mean(
            selector_string="", timeout=10.0)
        logging.info(f"TX EVM result: {composite_rms_evm} dB")

        # === Step 6: Stop DUT TX ===
        digital_session.burst_pattern(start_label="disable_dut_tx",
                                       select_digital_function=True,
                                       wait_until_done=True, timeout=10.0)
        logging.info("DUT TX disabled")

        return {"composite_rms_evm_db": composite_rms_evm}

    except Exception as e:
        logging.error(f"TX EVM test failed: {e}")
        raise

    finally:
        # === Step 7: Cleanup — reverse order of initialization ===
        if rfmx_wlan is not None:
            rfmx_wlan.dispose()
        if rfmx_instr is not None:
            rfmx_instr.close()
        if digital_session is not None:
            digital_session.close()
        if dcpower_session is not None:
            try:
                for ch in dcpower_session.channels:
                    ch.output_enabled = False
                dcpower_session.abort()
            except Exception:
                pass
            dcpower_session.close()
        logging.info("All sessions closed")
```

---

## Test Architecture: RX Test (DUT Receives)

In an RX test, the signal generator (RFSG) transmits a known signal to the DUT, and the DUT's receiver performance is evaluated (e.g., PER, RSSI, BER).

### Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: DCPower — Power ON the DUT                             │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Digital — Configure DUT to RX mode                     │
│          SPI/RFFE: set band, channel, RX gain, LNA mode         │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: RFSG — Configure signal generator                      │
│          Load waveform, set frequency, power, IQ rate            │
│          Export start trigger on PXI line (optional)             │
│          Initiate generation                                     │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Wait — Allow DUT to receive packets                    │
│          time.sleep() or poll DUT status register                │
├─────────────────────────────────────────────────────────────────┤
│  Step 5: Digital — Read DUT RX results                           │
│          SPI/RFFE read: RSSI, PER counter, packet count          │
├─────────────────────────────────────────────────────────────────┤
│  Step 6: RFSG — Stop generation                                  │
│          Abort generation                                        │
├─────────────────────────────────────────────────────────────────┤
│  Step 7: DCPower — Power OFF the DUT (in finally block)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Test Architecture: TX Test with Interferer / Blocker

When testing DUT RX with an interferer, two RFSG instruments may be needed (wanted signal + interferer), or a single RFSG with combined waveform.

### Execution Order

```
Step 1: DCPower — Power ON DUT
Step 2: Digital — Configure DUT to RX mode
Step 3: RFSG #1 — Configure wanted signal (at DUT RX frequency)
Step 4: RFSG #2 — Configure interferer signal (at offset frequency)
Step 5: Synchronize both RFSG start triggers (or use master/slave)
Step 6: Initiate both generators simultaneously
Step 7: Wait → Read DUT performance
Step 8: Abort generators → Power OFF
```

---

## Trigger Wiring Conventions

### PXI Backplane Trigger Lines

PXI chassis provides 8 shared trigger lines (`PXI_Trig0` through `PXI_Trig7`) accessible by all instruments in the chassis.

**Recommended Conventions**:

| Trigger Line | Convention | Description |
|---|---|---|
| `PXI_Trig0` | **RFSG Start → RFmx** | Signal generator start trigger → analyzer acquisition trigger |
| `PXI_Trig1` | **DCPower Source Complete** | SMU signals power is stable |
| `PXI_Trig2` | **Digital Pattern Event** | DUT TX enable → analyzer trigger |
| `PXI_Trig3` | **Marker Event** | RFSG waveform marker (payload start) |
| `PXI_Trig4–7` | **Available** | User-defined |

> **Note**: These are conventions, not requirements. Any trigger line can be used for any purpose, but consistent naming helps code readability.

### Trigger Wiring Rules

1. **One exporter per line** — Only one instrument can drive a trigger line at a time. Multiple instruments can import (listen on) the same line.
2. **Edge polarity must match** — If the exporter sends a rising edge, all importers must be configured for rising edge.
3. **Export before arm** — The exporting instrument must be configured to export the trigger before `initiate()` is called.
4. **Arm before trigger** — The importing instrument must be armed (`initiate()`) before the trigger fires, or it will miss the trigger.

### Trigger String Formats

| Format | Example | Use |
|---|---|---|
| PXI backplane | `"PXI_Trig0"` | Cross-instrument sync within chassis |
| Device-qualified | `"/VST1/PXI_Trig0"` | When exporting from a specific device |
| Front panel | `"PFI0"` | External cable connections |
| PXI Star | `"PXI_STAR"` | High-speed star trigger (timing-critical) |

---

## Trigger Types by Instrument

| Instrument | Can Export | Can Import | Common Export Signal |
|---|---|---|---|
| **RFSG** | ✅ | ✅ | Start Trigger, Marker Event, Script Trigger |
| **RFmx** | ❌ (analyzer) | ✅ | — (receives triggers only) |
| **DCPower** | ✅ | ✅ | Source Complete Event, Sequence Advance |
| **Digital** | ✅ | ✅ | Pattern Opcode Event 0–3, Conditional Jump Trigger |

---

## SA Trigger Selection Rule (when NI-Digital instrument is present)

When the test involves an NI-Digital pattern instrument, the Signal Analyzer (RFmx) trigger can originate from the digital device. **You MUST ask the user** which SA trigger type to use before generating code:

| Trigger Option | Description | When to Use |
|---|---|---|
| **Digital Edge trigger (from Pattern Opcode Event)** | Digital instrument exports a Pattern Opcode Event (0–3) on a PXI trigger line; SA arms on that line. | Most precise timing — use when the digital pattern has an opcode event at the exact moment the DUT is commanded to transmit or switch on. |
| **IQ Power Edge trigger** | SA self-triggers when DUT output power rises above a threshold. | When no hardware trigger is available, or when you need to detect the DUT signal directly in the IQ domain. |
| **Software trigger** | SA triggered programmatically after the digital pattern burst completes. | Simplest option, but least precise timing. Acceptable for non-time-critical measurements. |

> **Default when the user specifies "trigger from digital device"**: Use Digital Edge trigger from **Pattern Opcode Event 0**, exported on `PXI_Trig0`, rising edge. Ask the user to confirm the event number and PXI line if not specified.

---

### Digital Pattern Opcode Event Export

NI-Digital instruments can export **Pattern Opcode Event 0–3** on PXI trigger lines. A Pattern Opcode Event fires at a specific point within the digital pattern (marked by an opcode in the `.digipat` file). This provides precise timing correlation between the DUT command and the SA acquisition.

| Event | Export Property | Typical Use |
|---|---|---|
| Pattern Opcode Event 0 | `exported_patterns.pattern_opcode_event0.output_terminal` | SA trigger — fires when DUT is commanded to TX/switch on |
| Pattern Opcode Event 1 | `exported_patterns.pattern_opcode_event1.output_terminal` | Secondary marker (e.g., payload start) |
| Pattern Opcode Event 2–3 | `exported_patterns.pattern_opcode_event2/3.output_terminal` | User-defined |

```python
# Export Pattern Opcode Event 0 on PXI_Trig0 (Digital → SA trigger)
digital_session.exported_patterns.pattern_opcode_event0.output_terminal = "/HSD_6571_C1_S02/PXI_Trig0"
```

```c
/* C API equivalent */
niDigital_ExportSignal(
    vi,
    NIDIGITAL_VAL_PATTERN_OPCODE_EVENT,
    "patternOpcodeEvent0",
    "PXI_Trig0");
```

```python
# SA arms on PXI_Trig0 digital edge (Rising)
rfmx_specan.set_trigger_type(selector_string="", trigger_type=niRFmxSpecAn.TriggerType.DIGITAL_EDGE)
rfmx_specan.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig0")
rfmx_specan.set_digital_edge_trigger_edge(selector_string="", edge=niRFmxSpecAn.DigitalEdgeTriggerEdge.RISING)
```

---

## Multi-Instrument Synchronization Patterns

### Pattern 1: Simple TX Test (Digital → RFmx)

```
Digital: burst "enable_tx" pattern
  → DUT begins transmitting
  → RFmx: IQ Power Edge trigger (self-triggered on signal appearance)
```

This is the simplest pattern. No PXI trigger wiring needed — the analyzer self-triggers when it detects the DUT's signal.

```python
# RFmx self-trigger configuration
rfmx_wlan.set_trigger_type(selector_string="",
                             trigger_type=niRFmxWLAN.TriggerType.IQ_POWER_EDGE)
rfmx_wlan.set_iq_power_edge_trigger_level(selector_string="", level=-20.0)
rfmx_wlan.set_iq_power_edge_trigger_slope(selector_string="",
                                             slope=niRFmxWLAN.IQPowerEdgeTriggerSlope.RISING)
```

### Pattern 2: Synchronized TX Test via Pattern Opcode Event (Digital → PXI → RFmx)

```
Digital: export Pattern Opcode Event 0 on PXI_Trig0 (fires at opcode in pattern)
RFmx: arm digital edge trigger on PXI_Trig0
Digital: burst pattern → opcode fires Pattern Opcode Event 0 → PXI_Trig0 → RFmx acquires
```

More precise timing than self-trigger. The Pattern Opcode Event in the `.digipat` file fires at the exact vector where the DUT is commanded to transmit, giving sub-microsecond trigger accuracy.

```python
# Digital: export Pattern Opcode Event 0 on PXI_Trig0
digital_session.exported_patterns.pattern_opcode_event0.output_terminal = "/PXI1Slot5/PXI_Trig0"

# RFmx: import trigger from PXI_Trig0
rfmx_wlan.set_trigger_type(selector_string="",
                             trigger_type=niRFmxWLAN.TriggerType.DIGITAL_EDGE)
rfmx_wlan.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig0")
rfmx_wlan.set_digital_edge_trigger_edge(selector_string="",
                                           edge=niRFmxWLAN.DigitalEdgeTriggerEdge.RISING)
rfmx_wlan.set_trigger_delay(selector_string="", delay=0.0)  # adjust if DUT has ramp-up time
```

### Pattern 3: RX Test with RFSG (RFSG → PXI → RFmx or DUT)

```
RFSG: export start trigger on PXI_Trig0
RFSG: initiate() → generation starts → trigger fires
DUT: receives signal, processes, reports via Digital read
```

```python
# RFSG: export start trigger
rfsg_session.triggers.start_trigger.export_output_terminal = "/VST1/PXI_Trig0"
rfsg_session.initiate()  # Trigger fires at generation start
```

### Pattern 4: Power-Sequenced Start (DCPower → Digital → RFSG → RFmx)

```
DCPower: source voltage, export SOURCE_COMPLETE on PXI_Trig1
Digital: wait for PXI_Trig1, then burst DUT config pattern
RFSG: wait for pattern complete on PXI_Trig2, then generate
RFmx: wait for RFSG start on PXI_Trig0, then acquire
```

This is the most complex pattern — a cascading trigger chain that ensures correct sequencing without software polling delays.

---

## RFmx Personality Exclusion Rule

> **Critical**: Only one RFmx personality session may be active per physical instrument at a time.

If the test requires multiple measurement types (e.g., WLAN EVM + SpecAn ACP on the same VST):

```
❌ WRONG: Run WLAN and SpecAn simultaneously
✅ CORRECT: Run WLAN test → close WLAN session → Run SpecAn test → close SpecAn session
```

**Implementation**:
```python
# Test 1: WLAN EVM
def test_wlan_evm(resource_name, ...):
    rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name=resource_name, option_string="")
    rfmx_wlan = rfmx_instr.get_rfmx_wlan_signal("WLAN_Signal")
    # ... configure, measure, fetch ...
    rfmx_wlan.dispose()
    rfmx_instr.close()  # Fully close before next personality

# Test 2: SpecAn ACP (same physical instrument)
def test_specan_acp(resource_name, ...):
    rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name=resource_name, option_string="")
    rfmx_specan = rfmx_instr.get_rfmx_specan_signal("SpecAn_Signal")
    # ... configure, measure, fetch ...
    rfmx_specan.dispose()
    rfmx_instr.close()
```

---

## Cleanup Order

Always clean up in **reverse order** of initialization:

```
1. (Last initialized) RFmx → dispose personality, close instrument
2. RFSG → abort, close
3. Digital → close
4. (First initialized) DCPower → disable output, abort, close
```

This ensures that high-level measurement/generation sessions are torn down before the DUT power is removed, preventing undefined DUT behavior.

---

## Common Multi-Instrument Pitfalls

1. **Trigger race condition** — The importing instrument must be armed (`initiate()`) before the exporting instrument fires the trigger. If the trigger fires first, the importer misses it and hangs waiting.
2. **Forgetting trigger delay** — DUTs often have a ramp-up time between TX enable and stable output. Use `trigger_delay` on the analyzer to skip the ramp.
3. **Multiple exporters on same line** — Only one instrument can drive a PXI trigger line. Two exporters cause electrical conflict.
4. **Power-off before session close** — If DCPower disables output while RFSG/RFmx are still active, measurements may capture noise or transients. Close measurement sessions first.
5. **Personality collision** — Accidentally opening two RFmx personalities on the same instrument causes driver errors.
6. **Software timing assumptions** — Never rely on `time.sleep()` for synchronization between instruments. Use hardware triggers for repeatable timing.
