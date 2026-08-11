# STIL to Pattern Source — Mapping & Format Rules

## STIL Value Mapping

`.digipatsrc` files accept **only** these five values: `0`, `1`, `L`, `H`, `X`.  
Any STIL value outside this set must be converted to `X`.

| STIL Value | digipatsrc Value | Notes                              |
|------------|-----------------|------------------------------------|
| 0          | 0               | Drive low                          |
| 1          | 1               | Drive high                         |
| L          | L               | Expect low                         |
| H          | H               | Expect high                        |
| X          | X               | Don't care                         |
| Z          | **X**           | High impedance → mapped to X       |
| T          | **X**           | Tristate → mapped to X             |
| P          | **X**           | Pulse → mapped to X                |
| *(other)*  | **X**           | Any unrecognized value → mapped to X |


### Default Values for Unmapped Signals

| Signal Name Contains | Default Value |
|----------------------|---------------|
| `CLEAR`              | `1`           |
| `CLK`                | `0`           |
| All others           | `X`           |

---

## Pinmap File Loading

The pinmap CSV/text maps STIL signals to tester pins.

**Skip rules:**
- `Remove? = true` → skip entirely
- Signal name contains `LATCH` → skip

**Column name flexibility** (first match wins):

| Purpose          | Possible Column Names                                                        |
|------------------|-----------------------------------------------------------------------------|
| Tester pin       | `Group/Alias Name`, `Group_Alias_Name`, `GroupName`, `Group`, `TesterPin`, `Pin` |
| STIL signal      | `Signal Name`, `Signal_Name`, `SignalName`, `Signal`                        |
| Original signal  | `Original Signal Name (without bus index values)`, `Original_Signal_Name`, `OriginalSignal`, `STILSignal` |
| Direction        | `Direction`, `Dir`, `Type`                                                  |
| Is Scan          | `Is Scan?`, `Is_Scan`, `IsScan`, `Scan`                                    |
| Remove           | `Remove?`, `Remove`, `Skip`, `Exclude`                                      |

**Mapping key:** `original_signal → tester_pin` (original_signal falls back to group_name).

---

## Period Conversion

| STIL Unit | Scientific Multiplier |
|-----------|-----------------------|
| s         | E+0                   |
| ms        | E-3                   |
| us        | E-6                   |
| ns        | E-9                   |
| ps        | E-12                  |

**Parse:** `re.match(r'([\d.]+)\s*([a-z]+)', period_str)` → `{value}{exponent}`
e.g., `100ns` → `100E-9`

---

## Drive Format Selection

For each pin edge in a timeset:

| Condition                                  | Drive Format     | Special Values                    |
|--------------------------------------------|------------------|-----------------------------------|
| Has pulse (P) AND signal contains `SCLK`   | ReturnToLow      | On=0, Data=50E-9, Return=100E-9   |
| Has pulse (P) AND signal contains `CLEAR_SELECT` | ReturnToHigh | On=0, Data=50E-9, Return=100E-9   |
| Has pulse (P) AND other signal             | DriveNonReturn   | On=0, Data=0, Off=0 or 100E-9    |
| No pulse                                   | DriveNonReturn   | On=0, Data=0, Off=0 or 100E-9    |

- **Off value:** `0` for output signals, `100E-9` for input signals.

### CompareStrobe

| Signal Direction | Strobe Value |
|------------------|-------------|
| Output           | `40E-9`     |
| Input            | `0`         |

### DataSource

Always `Pattern`.

---

## digipatsrc File Structure

```
// Header comments (source file, target tester, date)

file_format_version 1.1;
timeset {timeset1}, {timeset2};

pattern _pattern_ ({pin1}, {pin2}, {pin3})
{
preconditionallSignals:
                         _default_WFT_                   X 1 0 X X;
                         -                               X 1 0 X X;
// Ann {* chain_test *}
pattern0:
                         _default_WFT_                   {default_values};
                         -                               {v1} {v2} ...;
                         -                               {v1} {v2} ...;
halt                     -                               {v1} {v2} ...;
}
```

- Last vector of the entire file starts with `halt`.
- CLK signals: `0` on last vector, `1` on intermediate vectors (when not in pattern data).
- Signal order in declaration follows pinmap file order.

---

## digitiming XML Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<TimingFile xmlns="http://www.ni.com/Semiconductor/Timing" schemaVersion="1.0">
  <TimingSheet>
    <TimeSets>
      <TimeSet name="{waveform_table_name}">
        <Period>{converted_period}</Period>
        <PinEdges>
          <PinEdge pin="{tester_pin}">
            <DriveNonReturn>  <!-- or ReturnToLow / ReturnToHigh -->
              <On>0</On>
              <Data>0</Data>
              <Off>100E-9</Off>
            </DriveNonReturn>
            <CompareStrobe>
              <Strobe>0</Strobe>  <!-- or 40E-9 for outputs -->
            </CompareStrobe>
            <DataSource>Pattern</DataSource>
          </PinEdge>
        </PinEdges>
      </TimeSet>
    </TimeSets>
  </TimingSheet>
</TimingFile>
```

---

## pinmap XML Structure (STIL-generated)

```xml
<?xml version="1.0" encoding="utf-8"?>
<PinMap xmlns="http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd"
        schemaVersion="1.0">
  <Instruments>
    <NIDigitalPatternInstrument name="Digital Pattern1" numberOfChannels="32" />
    <!-- default 3 digital + 2 DCPower instruments -->
  </Instruments>
  <Pins>
    <DUTPin name="{tester_pin}"/>  <!-- per mapped signal -->
  </Pins>
  <PinGroups>
    <PinGroup name="{signal_name}">   <!-- per output signal -->
      <PinReference pin="{tester_pin}"/>
    </PinGroup>
  </PinGroups>
</PinMap>
```

Output signals are identified by `signal.direction == OUTPUT` or `signal.is_scan_out == True`.
