# Code Mappings Reference

Read this file when the VI uses built-in nodes beyond the core control-flow examples in `SKILL.md`, when a `<Call>` targets an NI library, or when the diagram contains advanced LabVIEW constructs that need special handling.

## Common Node mappings

| LabVIEW Node | Python | C# |
|---|---|---|
| `Add` | `a + b` | `a + b` |
| `Subtract` | `a - b` | `a - b` |
| `Multiply` | `a * b` | `a * b` |
| `Divide` | `a / b` | `a / b` |
| `Quotient & Remainder` | `divmod(a, b)` | `(a / b, a % b)` |
| `Increment` | `x + 1` | `x + 1` or `x++` |
| `Decrement` | `x - 1` | `x - 1` or `x--` |
| `Greater?` | `a > b` | `a > b` |
| `Less?` | `a < b` | `a < b` |
| `Equal?` | `a == b` | `a == b` |
| `Not Equal?` | `a != b` | `a != b` |
| `And` | `a and b` | `a && b` |
| `Or` | `a or b` | `a \|\| b` |
| `Not` | `not a` | `!a` |
| `Select` | `a if selector else b` | `selector ? a : b` |
| `Compound Arithmetic` (add) | `sum([a, b, c, ...])` | `a + b + c + ...` |
| `Compound Arithmetic` (multiply) | `math.prod([a, b, c])` | `a * b * c` |
| `Concatenate Strings` | `a + b` or `"".join([...])` | `string.Concat(a, b)` or `$"{a}{b}"` |
| `String Length` | `len(s)` | `s.Length` |
| `String Subset` | `s[offset:offset+length]` | `s.Substring(offset, length)` |
| `Search and Replace String` | `s.replace(old, new)` | `s.Replace(old, new)` |
| `Number To Decimal String` | `str(n)` | `n.ToString()` |
| `Format Into String` | `f"..."` or `"...".format(...)` | `string.Format("...", ...)` |
| `Scan From String` | Parse with regex or type conversion | `int.Parse(s)`, `double.Parse(s)` |
| `Array Size` | `len(arr)` | `arr.Length` |
| `Index Array` | `arr[i]` | `arr[i]` |
| `Replace Array Subset` | `arr[i] = val` | `arr[i] = val` |
| `Insert Into Array` | `arr.insert(i, val)` | `list.Insert(i, val)` |
| `Delete From Array` | `del arr[i]` or `arr.pop(i)` | `list.RemoveAt(i)` |
| `Build Array` | `[a, b, c]` or `arr + [val]` | `new[] {a, b, c}` |
| `Initialize Array` | `[val] * n` | `Enumerable.Repeat(val, n).ToArray()` |
| `Sort 1D Array` | `sorted(arr)` | `Array.Sort(arr)` |
| `Reverse 1D Array` | `arr[::-1]` or `list(reversed(arr))` | `Array.Reverse(arr)` |
| `Bundle` | Tuple or dataclass construction | Tuple or object construction |
| `Unbundle` / `Unbundle By Name` | Tuple unpacking or attribute access | Property access |
| `Wait (ms)` | `time.sleep(ms / 1000)` | `Thread.Sleep(ms)` or `await Task.Delay(ms)` |
| `Tick Count (ms)` | `time.time() * 1000` | `Environment.TickCount` |
| `Random Number (0-1)` | `random.random()` | `new Random().NextDouble()` |
| `One Button Dialog` | `print(msg)` or `input(msg)` | `MessageBox.Show(msg)` |
| `Open/Create/Replace File` | `open(path, mode)` | `File.Open(path, mode)` |
| `Write to Text File` | `f.write(data)` | `File.WriteAllText(path, data)` |
| `Read from Text File` | `f.read()` | `File.ReadAllText(path)` |
| `Close File` | `f.close()` | `stream.Close()` |

## NI Driver Library Mappings

When a `<Call>` element's `target` matches an NI instrument driver or a common NI utility library, map it to the corresponding language-specific API:

| NI Driver / Library | Python Package | C# Namespace |
|---|---|---|
| **NI_XML.lvlib / XML Parser APIs** | `xml.etree.ElementTree`, `xml.dom.minidom`, `xml.xpath`-style helpers as needed | `System.Xml`, `System.Xml.Linq`, `System.Xml.Schema`, `System.Xml.XPath` |
| **DAQmx** | `nidaqmx` | `NationalInstruments.DAQmx` |
| **DCPower** (NI-DCPower / SMUs) | `nidcpower` | `NationalInstruments.ModularInstruments.NIDCPower` |
| **RFSG** (NI-RFSG / Signal Generators) | `nirfsg` | `NationalInstruments.ModularInstruments.NIRfsg` |
| **RFmx** (NI-RFmx / Signal Analyzers) | `niRFmxInstrMX` / `niRFmxSpecAnMX` / etc. | `NationalInstruments.RFmx.InstrMX` / `NationalInstruments.RFmx.SpecAnMX` / etc. |
| **Scope** (NI-SCOPE / Digitizers) | `niscope` | `NationalInstruments.ModularInstruments.NIScope` |
| **Digital** (NI-Digital / PPMU / Pattern) | `nidigital` | `NationalInstruments.ModularInstruments.NIDigital` |
| **DMM** (NI-DMM) | `nidmm` | `NationalInstruments.ModularInstruments.NIDmm` |
| **FGEN** (NI-FGEN / Function Generators) | `nifgen` | `NationalInstruments.ModularInstruments.NIFgen` |
| **Switch** (NI-SWITCH) | `niswitch` | `NationalInstruments.ModularInstruments.NISwitch` |
| **VISA / Serial / GPIB** | `pyvisa` | `NationalInstruments.Visa` |
| **IVI** | `pyvisa` (via IVI-C) | `Ivi.Driver` / instrument-specific IVI namespace |

**Identifying NI driver calls:** Look at the `target` attribute of `<Call>` elements. NI driver SubVIs typically have names starting with the driver prefix (for example, `niDCPower`, `niRFSG`, `niScope`, `niDigital`, `DAQmx`, `RFmx`). The `owning_palette_name` in the palette catalog also indicates the driver family.

**Common utility VI mappings:**
- `NI_XML.lvlib:*` DOM/document operations usually map to the target language's standard XML DOM, XPath, and schema-validation libraries.
- `Simple Error Handler.vi` usually maps to normal exception propagation, explicit result objects, logging, or console output rather than recreating a LabVIEW dialog.

## Handling complex / unsupported constructs

| LabVIEW Construct | Guidance |
|---|---|
| **Event Structure** | Map to an event loop or callback pattern. In Python, consider `asyncio` or a simple polling loop. In C#, use events/delegates or `async/await`. |
| **Producer/Consumer** | Map to a thread + queue pattern. Python: `threading.Thread` + `queue.Queue`. C#: `Task` + `BlockingCollection<T>`. |
| **State Machine** | Map to a `while` loop with a state variable and `match`/`switch` on the state enum. |
| **Property Nodes** | These interact with LabVIEW UI elements. Note them as comments. They typically have no equivalent in non-GUI code. If the user is building a GUI app, suggest the appropriate UI framework equivalent. |
| **Local / Global Variables** | Map to regular variables (local) or module-level / static variables (global). Note that LabVIEW globals have race condition implications and may need thread-safety comments. |
| **Functional Global (Action Engine)** | Map to a class with state (Python) or a static class with state (C#). |
| **Notifier / Semaphore** | Map to `threading.Event` / `threading.Semaphore` in Python, or `ManualResetEvent` / `SemaphoreSlim` in C#. |
| **VISA / Serial / GPIB** | Map to `pyvisa` in Python or `NationalInstruments.Visa` in C#. |
| **DAQmx** | Map to `nidaqmx` in Python or `NationalInstruments.DAQmx` in C#. |
| **DCPower** | Map to `nidcpower` in Python or `NationalInstruments.ModularInstruments.NIDCPower` in C#. |
| **RFSG** | Map to `nirfsg` in Python or `NationalInstruments.ModularInstruments.NIRfsg` in C#. |
| **RFmx** | Map to `niRFmxInstrMX` (and personality-specific modules) in Python or `NationalInstruments.RFmx.*` in C#. |
| **Scope / NI-SCOPE** | Map to `niscope` in Python or `NationalInstruments.ModularInstruments.NIScope` in C#. |
| **Digital / NI-Digital** | Map to `nidigital` in Python or `NationalInstruments.ModularInstruments.NIDigital` in C#. |
| **DMM / NI-DMM** | Map to `nidmm` in Python or `NationalInstruments.ModularInstruments.NIDmm` in C#. |
| **FGEN / NI-FGEN** | Map to `nifgen` in Python or `NationalInstruments.ModularInstruments.NIFgen` in C#. |
| **Switch / NI-SWITCH** | Map to `niswitch` in Python or `NationalInstruments.ModularInstruments.NISwitch` in C#. |
| **Waveform data type** | Create a simple class or dataclass with `t0` (timestamp), `dt` (time interval), and `y` (data array) fields. |