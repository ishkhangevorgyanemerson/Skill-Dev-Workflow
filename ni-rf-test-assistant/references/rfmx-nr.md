# NI-RFmx NR — 5G New Radio Measurement Driver Reference

> **Role**: Perform 3GPP 5G NR standard-specific measurements — ModAcc (EVM), ACP, SEM, TXP, and CHP. Supports FR1 (sub-6 GHz) and FR2 (mmWave). Use this personality when the DUT transmits a 5G NR signal and you need standard-aware demodulation.

---

## Session Lifecycle

```
Open RFmxInstrMX Session → Create NR Signal Configuration
  → Configure Common RF (frequency, reference level)
  → Configure Component Carrier (bandwidth, subcarrier spacing, cell ID)
  → Configure Bandwidth Part & Modulation
  → Configure Trigger → Select Measurement(s)
  → Initiate → Fetch Results → Close Session
```

### Python API

```python
import niRFmxInstr
import niRFmxNR

# 1. Open instrument session
rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name="VST1", option_string="")

# 2. Create NR signal configuration
rfmx_nr = rfmx_instr.get_rfmx_nr_signal("NR_Signal")

# 3. Configure common RF parameters
rfmx_nr.set_frequency(selector_string="", frequency=center_frequency)
rfmx_nr.set_reference_level(selector_string="", reference_level=reference_level)
rfmx_nr.set_external_attenuation(selector_string="", external_attenuation=0.0)

# 4. Configure frequency range
rfmx_nr.set_frequency_range(selector_string="", frequency_range=niRFmxNR.FrequencyRange.RANGE_1)

# 5. Configure component carrier
cc_selector = "carrier0"
rfmx_nr.set_component_carrier_bandwidth(selector_string=cc_selector,
                                          bandwidth=channel_bandwidth)
rfmx_nr.set_component_carrier_cell_id(selector_string=cc_selector,
                                        cell_id=cell_id)

# 6. Configure bandwidth part
bp_selector = "carrier0/bwp0"
rfmx_nr.set_bandwidth_part_subcarrier_spacing(selector_string=bp_selector,
                                                subcarrier_spacing=subcarrier_spacing)

# 7. Configure PUSCH (uplink) or PDSCH (downlink) modulation
pusch_selector = "carrier0/bwp0/pusch0"
rfmx_nr.set_pusch_modulation_type(selector_string=pusch_selector,
                                    modulation_type=niRFmxNR.PuschModulationType.QAM256)
rfmx_nr.set_pusch_number_of_resource_block_clusters(selector_string=pusch_selector,
                                                      number_of_clusters=1)
rfmx_nr.set_pusch_resource_block_offset(selector_string=pusch_selector,
                                          resource_block_offset=0)
rfmx_nr.set_pusch_number_of_resource_blocks(selector_string=pusch_selector,
                                              number_of_resource_blocks=num_rbs)

# 8. Configure trigger
rfmx_nr.set_trigger_type(selector_string="", trigger_type=niRFmxNR.TriggerType.DIGITAL_EDGE)
rfmx_nr.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig0")
rfmx_nr.set_digital_edge_trigger_edge(selector_string="", edge=niRFmxNR.DigitalEdgeTriggerEdge.RISING)

# 9. Select measurement
rfmx_nr.select_measurements(selector_string="",
                              measurements=niRFmxNR.MeasurementTypes.MODACC,
                              enable_all_traces=True)

# 10. Initiate
rfmx_nr.initiate(selector_string="", result_name="")

# 11. Fetch ModAcc results
composite_rms_evm_mean = rfmx_nr.modacc.results.fetch_composite_rms_evm_mean(
    selector_string="", timeout=10.0)
composite_peak_evm_maximum = rfmx_nr.modacc.results.fetch_composite_peak_evm_maximum(
    selector_string="", timeout=10.0)

# 12. Close
rfmx_nr.dispose()
rfmx_instr.close()
```

### C# API

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.NRMX;

// 1. Open instrument session
RFmxInstrMX rfmxInstr = new RFmxInstrMX("VST1", "");

// 2. Create NR signal configuration
RFmxNRMX rfmxNR = rfmxInstr.GetNRSignalConfiguration("NR_Signal");

// 3. Common RF
rfmxNR.SetFrequency("", centerFrequency);
rfmxNR.SetReferenceLevel("", referenceLevel);

// 4. Frequency range
rfmxNR.SetFrequencyRange("", RFmxNRMXFrequencyRange.Range1);

// 5. Component carrier
rfmxNR.SetComponentCarrierBandwidth("carrier0", channelBandwidth);
rfmxNR.SetComponentCarrierCellId("carrier0", cellId);

// 6. Bandwidth part
rfmxNR.SetBandwidthPartSubcarrierSpacing("carrier0/bwp0", subcarrierSpacing);

// 7. PUSCH modulation
rfmxNR.SetPuschModulationType("carrier0/bwp0/pusch0", RFmxNRMXPuschModulationType.Qam256);

// 8. Trigger
rfmxNR.SetTriggerType("", RFmxNRMXTriggerType.DigitalEdge);
rfmxNR.SetDigitalEdgeTriggerSource("", "PXI_Trig0");

// 9. Measurement
rfmxNR.SelectMeasurements("", RFmxNRMXMeasurementTypes.ModAcc, true);

// 10. Initiate & fetch
rfmxNR.Initiate("", "");
double compositeRmsEvmMean;
rfmxNR.ModAcc.Results.FetchCompositeRmsEvmMean("", 10.0, out compositeRmsEvmMean);

// 11. Close
rfmxNR.Dispose();
rfmxInstr.Close();
```

---

## 5G NR Configuration Hierarchy

NR configuration is hierarchical. Understanding the selector string structure is critical:

```
Signal
  └── Component Carrier (carrier0, carrier1, ...)
        ├── Cell ID
        ├── Channel Bandwidth
        └── Bandwidth Part (bwp0, bwp1, ...)
              ├── Subcarrier Spacing
              └── PUSCH / PDSCH (pusch0, pdsch0, ...)
                    ├── Modulation Type
                    ├── Resource Block Offset
                    └── Number of Resource Blocks
```

**Selector string examples**:
- Component carrier 0: `"carrier0"`
- Bandwidth part 0 of carrier 0: `"carrier0/bwp0"`
- PUSCH 0 of BWP 0, carrier 0: `"carrier0/bwp0/pusch0"`

---

## Frequency Range

| Range | Enum Value | Frequency Band | Typical Subcarrier Spacing |
|---|---|---|---|
| FR1 | `RANGE_1` | 410 MHz – 7.125 GHz | 15, 30, 60 kHz |
| FR2 | `RANGE_2` | 24.25 GHz – 52.6 GHz | 60, 120 kHz |

---

## Subcarrier Spacing

| Value (Hz) | Numerology (µ) | FR1 | FR2 |
|---|---|---|---|
| 15e3 | 0 | Yes | No |
| 30e3 | 1 | Yes | No |
| 60e3 | 2 | Yes | Yes |
| 120e3 | 3 | No | Yes |

---

## Channel Bandwidth (FR1)

| Subcarrier Spacing | Supported Bandwidths (MHz) |
|---|---|
| 15 kHz | 5, 10, 15, 20, 25, 30, 40, 50 |
| 30 kHz | 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100 |
| 60 kHz | 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100 |

---

## Measurement Types

### ModAcc (EVM)

Demodulates the NR signal and computes EVM per 3GPP specifications.

**Key Parameters**:
| Parameter | Method | Notes |
|---|---|---|
| Frequency Range | `set_frequency_range()` | FR1 or FR2 |
| Component Carrier Bandwidth | `set_component_carrier_bandwidth()` | In Hz |
| Subcarrier Spacing | `set_bandwidth_part_subcarrier_spacing()` | In Hz |
| Cell ID | `set_component_carrier_cell_id()` | 0–1007 |
| Modulation Type | `set_pusch_modulation_type()` | QPSK, QAM16, QAM64, QAM256 |
| Number of Resource Blocks | `set_pusch_number_of_resource_blocks()` | Allocation size |
| Resource Block Offset | `set_pusch_resource_block_offset()` | Starting RB |
| Averaging Count | `modacc.set_averaging_count()` | Number of slots to average |
| Measurement Length | `modacc.set_measurement_length()` | Number of slots |

**Fetch Results**:
| Result | Method | Units |
|---|---|---|
| Composite RMS EVM Mean | `fetch_composite_rms_evm_mean()` | % or dB |
| Composite Peak EVM Maximum | `fetch_composite_peak_evm_maximum()` | % or dB |
| Composite RMS EVM Std Dev | `fetch_composite_rms_evm_std_dev()` | % or dB |
| Frequency Error Mean | `fetch_frequency_error_mean()` | Hz |
| Symbol Clock Error Mean | `fetch_symbol_clock_error_mean()` | ppm |
| IQ Origin Offset Mean | `fetch_iq_origin_offset_mean()` | dBc |

### ACP (Adjacent Channel Power)

Measures power leakage into adjacent NR channels. Offset definitions follow 3GPP specifications.

**Key Parameters**: `channel_bandwidth`, NR-specific offset auto-configuration based on standard

**Fetch Results**: `carrier_absolute_power`, `lower_relative_power[]`, `upper_relative_power[]`

### SEM (Spectrum Emission Mask)

Validates out-of-band emissions against 3GPP NR mask definitions.

**Key Parameters**: Auto-configured from standard/bandwidth/frequency range

**Fetch Results**: `measurement_status` (pass/fail), per-offset `margin`, `peak_absolute_power`

### TXP (Transmit Power)

Measures average transmit power of the NR signal.

**Fetch Results**: `average_power_mean` (dBm)

---

## Required Parameters Checklist

| Parameter | Type | Required? | Notes |
|---|---|---|---|
| `resource_name` | string | **Yes** | e.g., `"VST1"` |
| `center_frequency` | float (Hz) | **Yes** | NR channel center frequency |
| `reference_level` | float (dBm) | **Yes** | Expected DUT power + margin |
| `frequency_range` | enum | **Yes** | FR1 or FR2 |
| `channel_bandwidth` | float (Hz) | **Yes** | NR channel bandwidth |
| `subcarrier_spacing` | float (Hz) | **Yes** | Must be valid for frequency range |
| `cell_id` | int | **Yes** | Physical cell ID (0–1007) |
| `modulation_type` | enum | **Yes** (for ModAcc) | QPSK, QAM16, QAM64, QAM256 |
| `number_of_resource_blocks` | int | **Yes** (for ModAcc) | Allocation size |
| `resource_block_offset` | int | **Yes** (for ModAcc) | Starting RB position |
| `measurement_type` | enum | **Yes** | MODACC, ACP, SEM, TXP |
| `trigger_type` | enum | **Yes** (multi-instrument) | DIGITAL_EDGE typical |
| `trigger_source` | string | **Yes** (if triggered) | e.g., `"PXI_Trig0"` |
| `external_attenuation` | float (dB) | Recommended | Cable/fixture loss |

---

## Error Handling Pattern

```python
rfmx_instr = None
rfmx_nr = None
try:
    rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name=resource_name, option_string="")
    logging.info(f"RFmx NR instrument session opened: {resource_name}")

    rfmx_nr = rfmx_instr.get_rfmx_nr_signal("NR_Signal")

    # ... configure carrier, BWP, PUSCH, trigger, measurement ...

    rfmx_nr.initiate(selector_string="", result_name="")
    logging.info("NR ModAcc measurement initiated")

    composite_rms_evm = rfmx_nr.modacc.results.fetch_composite_rms_evm_mean(
        selector_string="", timeout=10.0)
    logging.info(f"NR ModAcc EVM: {composite_rms_evm} dB")

except Exception as e:
    logging.error(f"RFmx NR error on {resource_name}: {e}")
    raise

finally:
    if rfmx_nr is not None:
        rfmx_nr.dispose()
    if rfmx_instr is not None:
        rfmx_instr.close()
        logging.info(f"RFmx NR session closed: {resource_name}")
```

---

## Common Pitfalls

1. **Selector string hierarchy** — Incorrectly formed selector strings (e.g., `"bwp0"` instead of `"carrier0/bwp0"`) cause configuration errors. Always use the full hierarchy path.
2. **Subcarrier spacing / bandwidth mismatch** — Not all subcarrier spacings are valid for all bandwidths. Consult the NR bandwidth table.
3. **FR1 vs FR2 configuration** — Different subcarrier spacing ranges, different SEM mask definitions, different ACP offset definitions. Always set `frequency_range` first.
4. **Cell ID dependency** — Cell ID affects scrambling and DM-RS sequences. Using the wrong cell ID causes EVM measurement to fail (unable to demodulate).
5. **PUSCH vs PDSCH** — Use PUSCH configuration for UE TX testing, PDSCH for gNB TX testing. Most DUT tests use PUSCH.
6. **Personality collision** — Cannot run NR personality simultaneously with SpecAn or WLAN on the same physical instrument. Split into separate test functions.
7. **Number of RBs** — Must be valid for the given bandwidth and subcarrier spacing combination. Use 3GPP table 5.3.2-1 (TS 38.104) for max RB counts.
