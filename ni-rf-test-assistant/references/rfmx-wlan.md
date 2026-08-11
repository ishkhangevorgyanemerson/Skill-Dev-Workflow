# NI-RFmx WLAN — 802.11 Measurement Driver Reference

> **Role**: Perform standard-specific 802.11 measurements — EVM (Error Vector Magnitude), TXP, SEM, Spectral Flatness, and more. Supports 802.11a/b/g/n/ac/ax/be. Use this personality when the DUT transmits a WLAN signal and you need standard-aware demodulation and analysis.

---

## Session Lifecycle

```
Open RFmxInstrMX Session → Create WLAN Signal Configuration
  → Configure Common RF (frequency, reference level)
  → Configure WLAN Standard & Channel
  → Configure Trigger → Select Measurement(s)
  → Initiate → Fetch Results → Close Session
```

### Python API

```python
import niRFmxInstr
import niRFmxWLAN

# 1. Open instrument session
rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name="VST1", option_string="")

# 2. Create WLAN signal configuration
rfmx_wlan = rfmx_instr.get_rfmx_wlan_signal("WLAN_Signal")

# 3. Configure common RF parameters
rfmx_wlan.set_frequency(selector_string="", frequency=center_frequency)
rfmx_wlan.set_reference_level(selector_string="", reference_level=reference_level)
rfmx_wlan.set_external_attenuation(selector_string="", external_attenuation=0.0)

# 4. Configure WLAN standard
rfmx_wlan.set_standard(selector_string="", standard=niRFmxWLAN.Standard.STANDARD_802_11_AX)

# 5. Configure channel bandwidth
rfmx_wlan.set_channel_bandwidth(selector_string="", channel_bandwidth=channel_bandwidth)

# 6. Configure OFDM modulation properties (802.11ax example)
rfmx_wlan.ofdm_modacc.set_mcs_index(selector_string="", mcs_index=mcs_index)
rfmx_wlan.ofdm_modacc.set_guard_interval_type(
    selector_string="",
    guard_interval_type=niRFmxWLAN.OfdmModAccGuardIntervalType.GUARD_INTERVAL_1_6)

# 7. Configure trigger
rfmx_wlan.set_trigger_type(selector_string="", trigger_type=niRFmxWLAN.TriggerType.DIGITAL_EDGE)
rfmx_wlan.set_digital_edge_trigger_source(selector_string="", source="PXI_Trig0")
rfmx_wlan.set_digital_edge_trigger_edge(selector_string="", edge=niRFmxWLAN.DigitalEdgeTriggerEdge.RISING)

# 8. Select measurement (e.g., OFDM ModAcc for EVM)
rfmx_wlan.select_measurements(
    selector_string="",
    measurements=niRFmxWLAN.MeasurementTypes.OFDM_MODACC,
    enable_all_traces=True)

# 9. Initiate
rfmx_wlan.initiate(selector_string="", result_name="")

# 10. Fetch EVM results
composite_rms_evm = rfmx_wlan.ofdm_modacc.results.fetch_composite_rms_evm_mean(
    selector_string="", timeout=10.0)

# 11. Close
rfmx_wlan.dispose()
rfmx_instr.close()
```

### C# API

```csharp
using NationalInstruments.RFmx.InstrMX;
using NationalInstruments.RFmx.WLANMX;

// 1. Open instrument session
RFmxInstrMX rfmxInstr = new RFmxInstrMX("VST1", "");

// 2. Create WLAN signal configuration
RFmxWLANMX rfmxWlan = rfmxInstr.GetWlanSignalConfiguration("WLAN_Signal");

// 3. Common RF parameters
rfmxWlan.SetFrequency("", centerFrequency);
rfmxWlan.SetReferenceLevel("", referenceLevel);

// 4. Standard and bandwidth
rfmxWlan.SetStandard("", RFmxWLANMXStandard.Standard802_11ax);
rfmxWlan.SetChannelBandwidth("", channelBandwidth);

// 5. Trigger
rfmxWlan.SetTriggerType("", RFmxWLANMXTriggerType.DigitalEdge);
rfmxWlan.SetDigitalEdgeTriggerSource("", "PXI_Trig0");

// 6. Select and configure measurement
rfmxWlan.SelectMeasurements("", RFmxWLANMXMeasurementTypes.OfdmModAcc, true);

// 7. Initiate and fetch
rfmxWlan.Initiate("", "");
double compositeRmsEvm;
rfmxWlan.OfdmModAcc.Results.FetchCompositeRmsEvmMean("", 10.0, out compositeRmsEvm);

// 8. Close
rfmxWlan.Dispose();
rfmxInstr.Close();
```

---

## Supported WLAN Standards

| Enum Value | Standard | Modulation | Notes |
|---|---|---|---|
| `STANDARD_802_11_A` | 802.11a | OFDM | 5 GHz, up to 54 Mbps |
| `STANDARD_802_11_B` | 802.11b | DSSS/CCK | 2.4 GHz, use DSSS measurements |
| `STANDARD_802_11_G` | 802.11g | OFDM | 2.4 GHz, up to 54 Mbps |
| `STANDARD_802_11_N` | 802.11n (Wi-Fi 4) | OFDM MIMO | HT, 20/40 MHz |
| `STANDARD_802_11_AC` | 802.11ac (Wi-Fi 5) | OFDM MIMO | VHT, 20/40/80/160 MHz |
| `STANDARD_802_11_AX` | 802.11ax (Wi-Fi 6/6E) | OFDMA | HE, 20/40/80/160 MHz |
| `STANDARD_802_11_BE` | 802.11be (Wi-Fi 7) | OFDMA | EHT, 20/40/80/160/320 MHz |

---

## Measurement Types

### OFDM ModAcc (EVM)

Demodulates the OFDM signal and computes EVM (Error Vector Magnitude). This is the primary measurement for TX quality.

**Key Parameters**:
| Parameter | Method | Notes |
|---|---|---|
| Standard | `set_standard()` | Must match DUT output |
| Channel Bandwidth | `set_channel_bandwidth()` | 20e6, 40e6, 80e6, 160e6, 320e6 |
| MCS Index | `ofdm_modacc.set_mcs_index()` | Modulation & coding scheme (0–11 for ax) |
| Guard Interval | `ofdm_modacc.set_guard_interval_type()` | 0.8µs, 1.6µs, 3.2µs for ax |
| Number of Spatial Streams | `set_number_of_spatial_streams()` | MIMO configurations |
| Averaging Count | `ofdm_modacc.set_averaging_count()` | Number of packets to average |

**Fetch Results**:
| Result | Method | Units |
|---|---|---|
| Composite RMS EVM Mean | `fetch_composite_rms_evm_mean()` | dB |
| Data RMS EVM Mean | `fetch_data_rms_evm_mean()` | dB |
| Pilot RMS EVM Mean | `fetch_pilot_rms_evm_mean()` | dB |
| Number of Symbols Used | `fetch_number_of_symbols_used()` | count |
| Frequency Error Mean | `fetch_frequency_error_mean()` | Hz |
| Symbol Clock Error Mean | `fetch_symbol_clock_error_mean()` | ppm |
| IQ Origin Offset Mean | `fetch_iq_origin_offset_mean()` | dBc |

### DSSS ModAcc (for 802.11b)

Use instead of OFDM ModAcc for DSSS/CCK modulated signals (802.11b).

**Key Parameters**: `data_rate` (1, 2, 5.5, 11 Mbps)

**Fetch Results**: `evm_rms_mean`, `evm_peak_mean`, `frequency_error_mean`

### TXP (Transmit Power)

Measures the burst power of the WLAN packet.

**Key Parameters**: `measurement_interval`, `maximum_measurement_interval`

**Fetch Results**: `average_power_mean` (dBm), `peak_power_maximum` (dBm)

### SEM (Spectrum Emission Mask)

Checks out-of-band emissions against the standard-defined mask. The mask limits are automatically applied based on the selected standard and channel bandwidth.

**Key Parameters**: Standard and channel bandwidth (mask auto-configured)

**Fetch Results**: `measurement_status` (pass/fail), per-offset `margin`, `peak_absolute_power`

### Spectral Flatness

Measures the variation in subcarrier power across the channel — critical for OFDM transmitter quality.

**Fetch Results**: `margin` (dB, relative to mask), `per_subcarrier_power` array

---

## Channel Bandwidth Values

| Standard | Supported Bandwidths (Hz) |
|---|---|
| 802.11a/g | 20e6 |
| 802.11n | 20e6, 40e6 |
| 802.11ac | 20e6, 40e6, 80e6, 160e6 |
| 802.11ax | 20e6, 40e6, 80e6, 160e6 |
| 802.11be | 20e6, 40e6, 80e6, 160e6, 320e6 |

---

## Required Parameters Checklist

| Parameter | Type | Required? | Notes |
|---|---|---|---|
| `resource_name` | string | **Yes** | e.g., `"VST1"` |
| `center_frequency` | float (Hz) | **Yes** | Channel center frequency |
| `reference_level` | float (dBm) | **Yes** | Expected DUT TX power + margin |
| `standard` | enum | **Yes** | 802.11a/b/g/n/ac/ax/be |
| `channel_bandwidth` | float (Hz) | **Yes** | Must match standard capability |
| `measurement_type` | enum | **Yes** | OFDM_MODACC, TXP, SEM, etc. |
| `mcs_index` | int | **Yes** (for EVM) | Modulation & coding scheme |
| `guard_interval_type` | enum | Recommended (for ax/be) | 0.8 / 1.6 / 3.2 µs |
| `trigger_type` | enum | **Yes** (multi-instrument) | DIGITAL_EDGE typical |
| `trigger_source` | string | **Yes** (if triggered) | e.g., `"PXI_Trig0"` |
| `external_attenuation` | float (dB) | Recommended | Cable/fixture loss |

---

## Error Handling Pattern

```python
rfmx_instr = None
rfmx_wlan = None
try:
    rfmx_instr = niRFmxInstr.RFmxInstrMX(resource_name=resource_name, option_string="")
    logging.info(f"RFmx WLAN instrument session opened: {resource_name}")

    rfmx_wlan = rfmx_instr.get_rfmx_wlan_signal("WLAN_Signal")

    # ... configure standard, bandwidth, trigger, measurement ...

    rfmx_wlan.initiate(selector_string="", result_name="")
    logging.info(f"WLAN {measurement_type} measurement initiated")

    # ... fetch results ...
    logging.info(f"WLAN EVM result: {composite_rms_evm} dB")

except Exception as e:
    logging.error(f"RFmx WLAN error on {resource_name}: {e}")
    raise

finally:
    if rfmx_wlan is not None:
        rfmx_wlan.dispose()
    if rfmx_instr is not None:
        rfmx_instr.close()
        logging.info(f"RFmx WLAN session closed: {resource_name}")
```

---

## Common Pitfalls

1. **Standard mismatch** — Setting `802.11ac` when the DUT transmits `802.11ax` causes demodulation failure. Always confirm the standard with the user.
2. **MCS index out of range** — Each standard has a different valid MCS range. 802.11ax supports 0–11; 802.11ac supports 0–9.
3. **Channel bandwidth mismatch** — Must match the actual DUT transmission bandwidth. Using 40 MHz config for a 20 MHz signal causes incorrect results.
4. **Using OFDM ModAcc for 802.11b** — 802.11b uses DSSS modulation. Use DSSS ModAcc measurement instead.
5. **Personality collision** — Cannot run WLAN personality simultaneously with SpecAn or NR on the same physical instrument. Split into separate test functions.
6. **Reference level** — Set 5–10 dB above expected peak power to avoid ADC clipping, but not so high as to lose dynamic range.
