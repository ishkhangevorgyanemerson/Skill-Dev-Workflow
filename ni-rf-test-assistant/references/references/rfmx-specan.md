# NI-RFmx SpecAn — Spectrum Analyzer Driver Reference

> **Role**: Perform general-purpose spectrum measurements — Transmit Power (TXP), Adjacent Channel Power (ACP), Spectrum Emission Mask (SEM), Channel Power (CHP), Occupied Bandwidth (OBW), Harmonic, and more. Use this personality when the signal is not a recognized wireless standard, or when performing standard-agnostic power/spectral measurements.

---

## Session Lifecycle

```
Open RFmxInstrMX Session → Create SpecAn Signal Configuration
  → Configure Common (frequency, reference level, trigger)
  → Select Measurement Type → Configure Measurement-Specific Parameters
  → Initiate → Fetch Results → Close Session
```

### Python API

```python
import niRFmxInstr
import niRFmxSpecAn

# 1. Open the instrument session
rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name="VST1", option_string="")

# 2. Create a SpecAn signal configuration (named signal)
rfmx_specan = rfmx_instr.get_rfmx_specan_signal("SpecAn_Signal")

# 3. Configure common RF parameters
rfmx_specan.set_frequency(selector_string="", frequency=center_frequency)
rfmx_specan.set_reference_level(selector_string="", reference_level=reference_level)
rfmx_specan.set_external_attenuation(selector_string="", external_attenuation=0.0)

# 4. Configure digital edge trigger (for multi-instrument sync)
rfmx_specan.set_trigger_type(selector_string="", trigger_type=niRFmxSpecAn.TriggerType.DIGITAL_EDGE)
rfmx_specan.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig0")
rfmx_specan.set_digital_edge_trigger_edge(selector_string="", edge=niRFmxSpecAn.DigitalEdgeTriggerEdge.RISING)
rfmx_specan.set_trigger_delay(selector_string="", delay=0.0)

# 5. Select and configure measurement (e.g., TXP)
rfmx_specan.select_measurements(selector_string="",
                                 measurements=niRFmxSpecAn.MeasurementTypes.TXP,
                                 enable_all_traces=True)

rfmx_specan.txp.configuration.set_measurement_interval(selector_string="",
                                                         measurement_interval=1e-3)
rfmx_specan.txp.configuration.set_rbw_filter_bandwidth(selector_string="",
                                                         bandwidth=channel_bandwidth)

# 6. Initiate measurement
rfmx_specan.initiate(selector_string="", result_name="")

# 7. Fetch results
average_mean_power = rfmx_specan.txp.results.fetch_measurement(
    selector_string="", timeout=10.0
)

# 8. Close
rfmx_specan.dispose()
rfmx_instr.close()
```

### C# API

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.SpecAnMX;

// 1. Open instrument session
RFmxInstrMX rfmxInstr = new RFmxInstrMX("VST1", "");

// 2. Create SpecAn signal configuration
RFmxSpecAnMX rfmxSpecAn = rfmxInstr.GetSpecAnSignalConfiguration("SpecAn_Signal");

// 3. Configure common parameters
rfmxSpecAn.SetFrequency("", centerFrequency);
rfmxSpecAn.SetReferenceLevel("", referenceLevel);

// 4. Configure trigger
rfmxSpecAn.SetTriggerType("", RFmxSpecAnMXTriggerType.DigitalEdge);
rfmxSpecAn.SetDigitalEdgeTriggerSource("", "PXI_Trig0");
rfmxSpecAn.SetDigitalEdgeTriggerEdge("", RFmxSpecAnMXDigitalEdgeTriggerEdge.Rising);

// 5. Select measurement
rfmxSpecAn.SelectMeasurements("", RFmxSpecAnMXMeasurementTypes.Txp, true);
rfmxSpecAn.Txp.Configuration.SetMeasurementInterval("", 1e-3);

// 6. Initiate
rfmxSpecAn.Initiate("", "");

// 7. Fetch
double averageMeanPower;
rfmxSpecAn.Txp.Results.FetchMeasurement("", 10.0, out averageMeanPower, ...);

// 8. Close
rfmxSpecAn.Dispose();
rfmxInstr.Close();
```

---

## Supported Measurement Types

### TXP (Transmit Power)

Measures the average, peak, minimum, and maximum power of a signal within a specified measurement interval.

**Key Parameters**:
| Parameter | Method | Typical Value |
|---|---|---|
| Measurement Interval | `txp.configuration.set_measurement_interval()` | `1e-3` s (1 ms) |
| RBW Filter Bandwidth | `txp.configuration.set_rbw_filter_bandwidth()` | Signal bandwidth |
| Averaging Count | `txp.configuration.set_averaging_count()` | `10` |
| Averaging Type | `txp.configuration.set_averaging_type()` | `RMS` |

**Fetch Results**: `average_mean_power` (dBm), `peak_power` (dBm), `minimum_power` (dBm)

### ACP (Adjacent Channel Power)

Measures power in the main channel and adjacent/alternate channels. Key for ACLR (Adjacent Channel Leakage Ratio) testing.

**Key Parameters**:
| Parameter | Method | Typical Value |
|---|---|---|
| Number of Offsets | `acp.configuration.set_number_of_offsets()` | `2` (adjacent + alternate) |
| Channel Bandwidth | `acp.configuration.set_channel_bandwidth()` | Signal bandwidth in Hz |
| Offset Frequency | `acp.configuration.set_offset_frequency()` | Depends on standard |
| Offset Bandwidth | `acp.configuration.set_offset_bandwidth()` | Same as channel BW |
| RBW Filter Bandwidth | `acp.configuration.set_rbw_filter_bandwidth()` | Auto or explicit |
| Measurement Method | `acp.configuration.set_measurement_method()` | `NORMAL` or `DYNAMIC_RANGE` |

**Fetch Results**: `carrier_absolute_power` (dBm), `lower_relative_power[]` (dB), `upper_relative_power[]` (dB)

### SEM (Spectrum Emission Mask)

Validates that out-of-band emissions stay within a defined mask. Used for regulatory compliance testing.

**Key Parameters**:
| Parameter | Method | Typical Value |
|---|---|---|
| Number of Offsets | `sem.configuration.set_number_of_offsets()` | Standard-dependent |
| Offset Start/Stop Frequency | `sem.offset.set_start_frequency()` / `set_stop_frequency()` | Per offset band |
| Offset RBW | `sem.offset.set_rbw_filter_bandwidth()` | Standard-dependent |
| Offset Limit | `sem.offset.set_absolute_limit_start()` / `set_absolute_limit_stop()` | Mask limit in dBm/Hz |

**Fetch Results**: `measurement_status` (pass/fail), per-offset `margin` (dB), `peak_absolute_power` (dBm)

### CHP (Channel Power)

Measures total in-channel power.

**Key Parameters**: `integration_bandwidth`, `span`

**Fetch Results**: `absolute_power` (dBm), `power_spectral_density` (dBm/Hz)

### OBW (Occupied Bandwidth)

Measures the bandwidth containing a specified percentage (typically 99%) of total signal power.

**Key Parameters**: `percent_of_power` (typically `99.0`)

**Fetch Results**: `occupied_bandwidth` (Hz)

---

## Trigger Configuration

| Trigger Type | Use Case | Configuration |
|---|---|---|
| **None / Free Run** | Single-instrument, continuous signal | `set_trigger_type(NONE)` |
| **Digital Edge** | Multi-instrument sync via PXI backplane | `set_trigger_type(DIGITAL_EDGE)` + source + edge |
| **IQ Power Edge** | Self-triggered on signal power threshold | `set_trigger_type(IQ_POWER_EDGE)` + level + slope |
| **Software** | Manual or programmatic trigger | `set_trigger_type(SOFTWARE)` |

### Digital Edge Trigger (Most Common for Multi-Instrument)

```python
rfmx_specan.set_trigger_type(selector_string="", trigger_type=niRFmxSpecAn.TriggerType.DIGITAL_EDGE)
rfmx_specan.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig0")
rfmx_specan.set_digital_edge_trigger_edge(selector_string="", edge=niRFmxSpecAn.DigitalEdgeTriggerEdge.RISING)
rfmx_specan.set_trigger_delay(selector_string="", delay=0.0)  # seconds
```

### IQ Power Edge Trigger (Self-Triggered)

```python
rfmx_specan.set_trigger_type(selector_string="", trigger_type=niRFmxSpecAn.TriggerType.IQ_POWER_EDGE)
rfmx_specan.set_iq_power_edge_trigger_level(selector_string="", level=-20.0)  # dBm
rfmx_specan.set_iq_power_edge_trigger_slope(selector_string="", slope=niRFmxSpecAn.IQPowerEdgeTriggerSlope.RISING)
```

---

## Required Parameters Checklist

| Parameter | Type | Required? | Notes |
|---|---|---|---|
| `resource_name` | string | **Yes** | e.g., `"VST1"` |
| `center_frequency` | float (Hz) | **Yes** | Signal center frequency |
| `reference_level` | float (dBm) | **Yes** | Expected max signal power + margin |
| `measurement_type` | enum | **Yes** | TXP, ACP, SEM, CHP, or OBW |
| `channel_bandwidth` | float (Hz) | **Yes** (ACP, SEM, CHP) | Measurement bandwidth |
| `measurement_interval` | float (s) | **Yes** (TXP) | Acquisition length |
| `trigger_type` | enum | **Yes** (multi-instrument) | DIGITAL_EDGE typical |
| `trigger_source` | string | **Yes** (if triggered) | e.g., `"PXI_Trig0"` |
| `external_attenuation` | float (dB) | Recommended | Account for cables/fixtures |

---

## Error Handling Pattern

```python
rfmx_instr = None
rfmx_specan = None
try:
    rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name=resource_name, option_string="")
    logging.info(f"RFmx SpecAn instrument session opened: {resource_name}")

    rfmx_specan = rfmx_instr.get_rfmx_specan_signal("SpecAn_Signal")
    logging.info("SpecAn signal configuration created")

    # ... configure and measure ...

    rfmx_specan.initiate(selector_string="", result_name="")
    logging.info("SpecAn measurement initiated, waiting for results...")

    result = rfmx_specan.txp.results.fetch_measurement(selector_string="", timeout=10.0)
    logging.info(f"SpecAn TXP result: average power = {result} dBm")

except Exception as e:
    logging.error(f"RFmx SpecAn error on {resource_name}: {e}")
    raise

finally:
    if rfmx_specan is not None:
        rfmx_specan.dispose()
    if rfmx_instr is not None:
        rfmx_instr.close()
        logging.info(f"RFmx SpecAn session closed: {resource_name}")
```

---

## Common Pitfalls

1. **Reference level too low** — Causes signal clipping in the ADC. Set reference level ≥ expected peak power + 5 dB margin.
2. **Reference level too high** — Reduces dynamic range and measurement accuracy. Match reference level to expected signal power.
3. **Forgetting external attenuation** — Cable/fixture losses must be accounted for, or power readings will be incorrect.
4. **Wrong trigger source** — Ensure the trigger source string matches what the exporting instrument actually drives (e.g., `"PXI_Trig0"` not `"/PXI_Trig0"`). Check polarity.
5. **Selector string misuse** — For single-signal configurations, use empty string `""`. Named signals require proper selector string format.
6. **Timeout too short** — Use at least 10 seconds for fetch operations. Triggered measurements may take longer if waiting for an external event.
