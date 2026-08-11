# NI-RFSG — Signal Generator Driver Reference

> **Role**: Generate CW tones, modulated waveforms (from file or memory), or scripted multi-segment signals. Commonly used as a TX source for RX sensitivity tests, an interferer/blocker source, or a loopback signal source.

---

## Session Lifecycle

```
Open Session → Configure RF (frequency, power) → Load / Configure Waveform
  → Configure Triggers (export start trigger for sync) → Initiate Generation
  → Wait Until Done or Continuous → Abort → Close Session
```

### Python API

```python
import nirfsg

# 1. Open session
rfsg_session = nirfsg.Session(resource_name="VST1")

# 2. Configure RF parameters
rfsg_session.rf.frequency = center_frequency       # Hz, e.g. 2.412e9
rfsg_session.rf.power_level = power_level           # dBm, e.g. -10.0

# 3. Load and configure waveform
#    Option A: From TDMS file
rfsg_session.write_waveform_from_file(waveform_name="my_waveform",
                                       file_path=waveform_file_path)
#    Option B: From complex IQ array (numpy)
rfsg_session.write_waveform(waveform_name="my_waveform",
                            data=iq_data)  # numpy complex128 array

# 4. Configure waveform properties
rfsg_session.arb.selected_waveform = "my_waveform"
rfsg_session.arb.pre_filter_gain = -2.0  # dB headroom to avoid DAC clipping

# 5. Configure generation mode
rfsg_session.rf.generation_mode = nirfsg.GenerationMode.ARB_WAVEFORM

# 6. Export start trigger for multi-instrument sync (optional)
rfsg_session.triggers.start_trigger.export_output_terminal = "/VST1/PXI_Trig0"

# 7. Initiate generation
rfsg_session.initiate()

# ... (measurement happens on analyzer side) ...

# 8. Abort and close
rfsg_session.abort()
rfsg_session.close()
```

### C# API

```csharp
using NationalInstruments.ModularInstruments.NIRfsg;

// 1. Open session
NIRfsg rfsgSession = new NIRfsg("VST1", true, false);

// 2. Configure RF
rfsgSession.RF.Frequency = centerFrequency;
rfsgSession.RF.PowerLevel = powerLevel;

// 3. Load waveform from file
rfsgSession.Arb.WriteWaveformFromFile("myWaveform", waveformFilePath);

// 4. Select waveform and configure
rfsgSession.Arb.SelectedWaveform = "myWaveform";
rfsgSession.Arb.PreFilterGain = -2.0;

// 5. Generation mode
rfsgSession.RF.GenerationMode = RfsgGenerationMode.ArbWaveform;

// 6. Export start trigger
rfsgSession.Triggers.StartTrigger.ExportOutputTerminal =
    RfsgTriggerTerminal.PxiTriggerLine0;

// 7. Initiate
rfsgSession.Initiate();

// 8. Abort and close
rfsgSession.Abort();
rfsgSession.Close();
```

---

## Configuration Details

### Generation Modes

| Mode | Enum Value | Use Case |
|---|---|---|
| CW | `CW` | Simple tone generation, LO source |
| Arb Waveform | `ARB_WAVEFORM` | Single waveform playback (most common) |
| Script | `SCRIPT` | Multi-segment waveform sequencing with conditional branching |

### Waveform Loading

- **TDMS files**: Standard NI waveform format. Use `write_waveform_from_file()`.
- **In-memory IQ data**: Pass a NumPy `complex128` array via `write_waveform()`. The real part is I, imaginary is Q.
- **IQ Rate**: Set `rfsg_session.arb.iq_rate` to match the waveform sample rate.
- **Pre-filter gain**: Apply negative gain (e.g., `-2.0 dB`) to provide headroom and prevent DAC clipping, especially for high-PAPR signals like OFDM.

### Script-Based Generation

For multi-segment waveforms (e.g., preamble + payload + gap):

```python
# Write multiple waveforms
rfsg_session.write_waveform("preamble", preamble_iq)
rfsg_session.write_waveform("payload", payload_iq)

# Write generation script
script = """
script myScript
    repeat forever
        generate preamble
        generate payload
    end repeat
end script
"""
rfsg_session.arb.scripting.write_script(script)
rfsg_session.arb.scripting.selected_script = "myScript"
rfsg_session.rf.generation_mode = nirfsg.GenerationMode.SCRIPT
```

### Trigger Export

RFSG can export several trigger/event signals to synchronize with other instruments:

| Signal | Description | Common Use |
|---|---|---|
| **Start Trigger** | Fires when generation begins | Synchronize analyzer acquisition |
| **Marker Event** | Fires at a specific sample within the waveform | Mark payload start for gated acquisition |
| **Script Trigger** | External input to control script branching | Conditional generation |

Export terminals can be:
- PXI backplane: `PXI_Trig0` through `PXI_Trig7`
- Front panel: `PFI0`, `PFI1`
- Device-specific: `PXI_STAR`, `PXIe_DStarA`

---

## Required Parameters Checklist

| Parameter | Type | Required? | Notes |
|---|---|---|---|
| `resource_name` | string | **Yes** | e.g., `"VST1"`, `"PXI1Slot2"` |
| `center_frequency` | float (Hz) | **Yes** | Signal center frequency |
| `power_level` | float (dBm) | **Yes** | Output power at the RF port |
| `waveform_file_path` or `iq_data` | string / array | **Yes** (for ARB mode) | Waveform source |
| `iq_rate` | float (S/s) | **Yes** (for ARB mode) | Must match waveform sample rate |
| `generation_mode` | enum | **Yes** | CW, ARB_WAVEFORM, or SCRIPT |
| `pre_filter_gain` | float (dB) | Recommended | `-2.0` dB typical for OFDM |
| `trigger_export_terminal` | string | For multi-instrument | e.g., `"/VST1/PXI_Trig0"` |

---

## Error Handling Pattern

```python
rfsg_session = None
try:
    rfsg_session = nirfsg.Session(resource_name=resource_name)
    logging.info(f"RFSG session opened: {resource_name}")

    # ... configure and generate ...

    rfsg_session.initiate()
    logging.info("RFSG generation initiated")

except Exception as e:
    logging.error(f"RFSG error on {resource_name}: {e}")
    raise

finally:
    if rfsg_session is not None:
        rfsg_session.abort()
        rfsg_session.close()
        logging.info(f"RFSG session closed: {resource_name}")
```

---

## Common Pitfalls

1. **Forgetting to set IQ rate** — The IQ rate must match the waveform file's sample rate. Mismatched rates cause incorrect signal bandwidth.
2. **DAC clipping with OFDM** — Always apply negative pre-filter gain for high-PAPR waveforms (WLAN, NR).
3. **Trigger polarity mismatch** — Ensure the analyzer's trigger edge polarity matches the RFSG export edge (typically rising).
4. **Not aborting before reconfiguring** — Call `abort()` before changing frequency/power/waveform on an actively generating session.
5. **Resource name mismatch** — When using VST (Vector Signal Transceiver), RFSG and RFmx share the same physical hardware. Use the same resource name for both.
