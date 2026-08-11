# Channel Map to PinMap — Detailed Rules

This reference is intentionally rule-based.
Use only values explicitly present in the input channel map.
Do not use prior project knowledge or semantic guessing to rename pins or add XML structures.

---

## Section Detection

Treat the CSV as two ordered sections:

1. **Pin Table** beginning at the header:

```text
Net Name,SITE1,SITE2,...
```

2. **Relay Table** beginning at the header:

```text
RELAY,NET NAME,SITE1,SITE2,...
```

Blank rows and rows containing only commas should be ignored.

---

## Duplicate Handling

Exact duplicate rows may appear in the channel map.

Rule:

- remove exact duplicate rows
- keep the first occurrence
- preserve original order of the remaining rows

## Device Mapping Table

| Device Number | XML Element                  | device_type | numberOfChannels | channelList format        |
|---------------|------------------------------|-------------|------------------|---------------------------|
| 6571          | NIDigitalPatternInstrument   | HSD         | 32               | —                         |
| 4309          | NIDAQmxTask (AnalogInputVoltage)  | DAC    | —                | `{name}/ai0:31`           |
| 4463          | NIDAQmxTask (AnalogOutputVoltage) | DSA    | —                | `{name}/ao0:1`            |
| 4163          | NIDCPowerInstrument          | SMU         | 24               | —                         |
| 2567          | NIRelayDriverModule          | RELAY       | 64 (controlLines)| —                         |

`device_name` = `{device_type}_{device_number}_C1_S{section}` (section = two digits after "S").

---

## Instrument Extraction Pseudocode

```
for each cell value in SITE columns of Pin Table:
    parse cell → (device_number, section, channel_info)
    # e.g., "6571_S14_DIO_4" → (6571, "S14", 4)
    # e.g., "4163_S03_HI_CH14" → (4163, "S03", 14)

    key = (device_number, section)
    if key not in instruments:
        device_type = DEVICE_MAP[device_number].device_type
        device_name = f"{device_type}_{device_number}_C1_{section}"
        instruments[key] = device_name
```

---

## Pin Sanitization

```
def sanitize_pin(net_name, device_type):
    name = re.sub(r'[^A-Za-z0-9]', '_', net_name)   # non-alnum → _
    name = name.rstrip('_')                            # strip trailing _
    if name and name[0].isdigit():
        name = f"{device_type}_{name}"                 # prefix digits
    return name

# Skip any row where Net Name == "GND"
```

Important:

- sanitization is purely syntactic
- do **not** convert names to domain aliases
- examples of forbidden inference:
  - `4163_AVDD_HI` → `AVDD_DVDD`
  - `6571_SCK` → `SCLK_PPMU`
  - `6571_nCS` → `nCS_PPMU`

If the channel map says `6571_SCK`, the sanitized pin should stay derived from that source text.

---

## Pin Grouping

```
groups = {}
for pin in all_pins:
    prefix = common_name_prefix(pin)   # e.g., "DAC" from "DAC_A3", "DAC_B4"
    groups.setdefault(f"ALL_{prefix}", []).append(pin)
```

Use deterministic normalization only.
Do not invent custom logical groups such as `ALL_SPI_PINS` or `ALL_PWR_PINS` unless such grouping rules are explicitly provided by another input source.

---

## Relay Combination

```
# Group relay rows by Net Name
for net_name, relay_rows in group_by_net_name(relay_table):
    relay_numbers = [extract_relay_number(row) for row in relay_rows]
    # extract_relay_number: "K3" → 3

    if len(relay_numbers) > 1:
        site_relay = "K" + "_".join(str(n) for n in relay_numbers)
        # e.g., K1 + K2 → "K1_2"
    else:
        site_relay = f"K{relay_numbers[0]}"
        # e.g., K3 → "K3"
```

      Only create:

      - one `SiteRelay` per combined relay net
      - one `RelayGroup` named `All_Relays`

      Do not infer additional relay groupings such as `K1_8`, `K9_16`, or similar rollups.

---

## Channel Extraction

```
def extract_channel(cell_value, device_number, device_name):
    if "CH" in cell_value:
        ch = re.search(r'CH(\d+)', cell_value).group(1)
    else:
        ch = cell_value.rsplit('_', 1)[-1].rstrip('+- ')

    if device_number == "4309":
        return f"{device_name}/ai{ch}"
    elif device_number == "4463":
        return f"{device_name}/ao{ch}"
    else:
        return ch
```

---

## Relay Control Line Extraction

```
# From "2567_S07_RELAY_CH44" → controlLine = "K44"
def extract_control_line(cell_value):
    ch = re.search(r'CH(\d+)', cell_value).group(1)
    return f"K{ch}"
```

---

## Connection Building

```xml
<!-- Pin Connection -->
<Connection pin="{sanitized_pin}"
            siteNumber="{site_index}"
            instrument="{device_name}"
            channel="{extracted_channel}" />

<!-- Relay Connection -->
<RelayConnection relay="{combined_relay_name}"
                 siteNumber="{site_index}"
                 relayDriverModule="{relay_device_name}"
                 controlLine="{K_number}" />
```

- `siteNumber` is 0-indexed: SITE1 → `0`, SITE2 → `1`, etc.

Do not emit `SystemConnection` entries unless the source channel map explicitly contains a defined system-pin section and the skill has explicit rules for it.

---

## Deterministic Script

The current deterministic implementation is:

- [Script/channelmap_to_pinmap.ps1](../Script/channelmap_to_pinmap.ps1)

Usage:

```powershell
powershell -ExecutionPolicy Bypass -File Script/channelmap_to_pinmap.ps1 \
  -InputCsv <channel_map.csv> \
  -OutputPinmap <output/PinMap.pinmap>
```

---

## Verification Rules

Before reporting success, verify:

- output file exists
- output file is non-empty XML
- pin count matches the number of unique sanitized non-`GND` net names after duplicate removal
- site count matches the detected `SITE` columns
- each connection references a declared instrument
- relay connections reference only relays declared in `Relays`

If a generated file differs from an existing project pinmap, prefer the explicit channel map input over inferred historical naming.

---

## Full PinMap XML Assembly

```xml
<?xml version="1.0" encoding="utf-8"?>
<PinMap xmlns="http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        schemaVersion="1.2">
  <Instruments>
    <!-- one element per unique (device_number, section) -->
  </Instruments>
  <Pins>
    <!-- <DUTPin name="..." /> per sanitized net name (skip GND) -->
  </Pins>
  <PinGroups>
    <!-- <PinGroup name="ALL_{prefix}"> with <PinReference pin="..."/> -->
  </PinGroups>
  <Relays>
    <!-- <SiteRelay name="K1_2"/> per combined relay -->
  </Relays>
  <RelayGroups>
    <RelayGroup name="All_Relays">
      <!-- <RelayReference relay="..."/> for every SiteRelay -->
    </RelayGroup>
  </RelayGroups>
  <Sites>
    <!-- <Site siteNumber="0"/> ... siteNumber="N-1" -->
  </Sites>
  <Connections>
    <!-- Pin connections + Relay connections -->
  </Connections>
</PinMap>
```
