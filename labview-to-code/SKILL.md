---
name: labview-to-code
description: Analyze an existing LabVIEW VI or LabVIEW project and translate its dataflow logic into equivalent C# or Python code. Use this skill when the user asks to convert a LabVIEW VI, helper VI tree, or .lvproj to text-based code, port LabVIEW logic to C# or Python, reverse-engineer a VI into readable code, or understand what a VI does and express it in another language.
---

# LabVIEW VI to C# / Python Code Conversion

## Why this skill exists

LabVIEW programs are graphical dataflow diagrams stored in a proprietary binary format. They cannot be read as text directly. However, a VI can be exported to a proprietary **VI XML** representation that describes every node, wire, structure, and data type in the block diagram. This skill uses that XML to reconstruct the VI's logic and produce faithful, idiomatic C# or Python code.

## Hard requirements

1. **Always extract the VI XML first.** Never guess what a VI does. Use `get_vi_xml.py` to export the actual block diagram XML before writing any code.
2. **Preserve the logic exactly.** The output code must replicate the VI's dataflow semantics — same operations, same control flow, same data types. Do not simplify, optimize, or skip steps unless the user explicitly asks.
3. **Map LabVIEW constructs to idiomatic target-language patterns.** While the logic must be preserved, the code style should feel natural in C# or Python — not a mechanical transliteration of XML.
4. **Ask the user which language to target** if they did not specify. Default to Python if the user says "code" without specifying a language.
5. **Document the mapping.** Add a brief comment at the top of the generated file listing the source VI name and a summary of what it does.
6. **Validate the conversion environment before scaffolding.** Confirm the VI extractor runs, and confirm the target-language toolchain version before choosing a framework or project template.
7. **If the source is a `.lvproj`, inventory the whole project before coding.** Enumerate top-level VIs, helper VIs, and non-VI assets such as XML, XSD, INI, or test files that must be preserved in the converted output.
8. **Always finish with a conversion report.** The final deliverable must include a traceable source-to-output mapping showing each VI and where its logic ended up in the generated code.

## Workflow

### Step 0 — Confirm inputs

Collect from the user:

| Input | Required? | Default |
|-------|-----------|---------|
| Path to the `.vi` file or `.lvproj` file | Yes | — |
| Target language (C# or Python) | No | Python |
| Output file path | No | Same directory as the VI, with `.py` or `.cs` extension |
| Output shape (single file, package, or solution/project) | No | Same directory as source; for `.lvproj` C# conversions, adjacent solution/project |

If the user did not provide the source path, ask for it:

```
Please provide the full path to the .vi or .lvproj file you want to convert.
```

Use `ask_questions` if available to collect the target language and output preferences in one step.

As soon as the target language is known, read exactly one target-language guide:
- Python -> `references/python-guidance.md`
- C# -> `references/csharp-guidance.md`

Do not read the other language guide unless the user explicitly asks for comparison output or dual-language generation.

### Step 1 — Extract the VI XML (including SubVIs)

If the source is a `.lvproj`, read the project XML first and inventory all project-owned assets before extracting any VI XML.

**For `.lvproj` inputs:**
- Read the `.lvproj` file and enumerate all `<Item Type="VI">` entries.
- Separate top-level example or entry VIs from helper SubVIs.
- Record non-VI assets that affect behavior or runtime, such as `.xml`, `.xsd`, `.ini`, `.ctl`, or sample data files.
- If the project contains `.ctl` typedef or control-definition assets that are consumed by converted VIs, generate an equivalent target-language type such as a Python dataclass, Python enum, C# record, or C# enum.
- Decide the converted output shape before coding. For C# this usually means a solution with a core library plus a small executable or test project.
- Preserve the original asset relationships in the converted output, either by copying or linking runtime files.

This skill bundles its own VI extraction scripts. Use the `get_vi_xml.py` script from this skill's `scripts/` directory.

**Locating the script:** The extraction script is at:
```
.github/skills/labview-to-code/scripts/get_vi_xml.py
```
Use `file_search(query="**/labview-to-code/scripts/get_vi_xml.py")` to find the absolute path if needed.

**Python dependency:** The script requires `pywin32`. If not installed, run:
```powershell
python -m pip install pywin32
```

**LabVIEW path:** The script reads the LabVIEW executable path from `labview_path.txt` in this skill's root directory. If LabVIEW is installed at a non-default location, update this file.

**Running the extraction:**
```powershell
python "<absolute path to .github/skills/labview-to-code/scripts/get_vi_xml.py>" "<full path to .vi file>"
```

**Environment check before broad conversion:**
- Run the extractor on one representative VI first.
- If the user wants C#, check the installed .NET SDK version before selecting the target framework or templates.
- If the user wants Python, verify the selected interpreter can import any required packages.

If the script returns a non-zero exit code, report the error to the user and stop.

Save the extracted XML mentally (or in a session note) — you will reference it throughout the conversion.

**Recursive SubVI extraction:** After extracting the top-level VI, scan the XML for all `<Call>` elements. For each `<Call>`:
- If the `target` matches an NI driver/library function (see NI Driver Library Mappings in Step 4), skip — it will be mapped to a library API call.
- If the `target` is a custom user VI (project-local SubVI), extract it too using `get_vi_xml.py` with its full path. Repeat this process for any SubVIs found inside those SubVIs.
- Build a complete list of all VIs to convert before starting code generation.

**Resolving SubVI paths:** The `target` attribute in `<Call>` typically contains the VI filename (e.g., `HelperSubVI.vi`). To find the full path:
- Search the workspace for the file: `file_search(query="**/HelperSubVI.vi")`
- If the SubVI is part of a library (`.lvlib` or `.lvclass`), the `target` will include the library path (e.g., `MyLib.lvlib:HelperSubVI.vi`). Search accordingly.
- If the file cannot be found, ask the user for the path.

### Step 2 — Analyze the VI structure

**Before analyzing the XML, read `references/vixml-format-26.1.yml`** in this skill's directory. This file is the authoritative specification for the VI XML schema — it defines every element type (`<VI>`, `<Control>`, `<Indicator>`, `<Constant>`, `<FixedConst>`, `<Node>`, `<Call>`, `<Structure>`, `<Tunnel>`, `<ShiftReg>`, `<CaseFrame>`, `<Condition>`, `<FreeLabel>`), wire naming conventions (`<uid>.<terminal_name>`), attribute ordering rules, and structure scoping semantics.

Read the extracted XML carefully and build a mental model of the VI. Identify:

1. **Front panel interface**
   - `<Control>` elements → these become function parameters or input variables
   - `<Indicator>` elements → these become return values or output variables
   - Note the `_name`, `type`, and `value` (default) of each

2. **Dataflow graph**
   - `<Node>` elements → built-in LabVIEW functions (Add, Multiply, String Length, etc.)
   - `<Call>` elements → SubVI calls (may map to library functions or separate methods)
   - `<Constant>` and `<FixedConst>` elements → literal values
   - Trace wires from outputs to inputs to determine execution order

3. **Control flow structures**
   - `<Structure _name="While Loop">` → `while` loop
   - `<Structure _name="For Loop">` → `for` loop
   - `<Structure _name="Case Structure">` → `if/elif/else` or `switch/case`
   - `<ShiftReg>` → loop-carried variables (previous-iteration state)
   - `<Tunnel>` → data crossing structure boundaries
   - `<Condition>` → loop termination condition

4. **Error chain**
   - Follow `error in` / `error out` wiring to understand the sequential execution order of nodes that would otherwise execute in parallel in pure dataflow

5. **Execution order**
   - LabVIEW is dataflow: nodes execute when all inputs are available. Use the wire dependency graph to determine a valid topological order for sequential code generation.

### Step 3 — Load the target-language guide

Once the target language is known, use the selected guide for:
- type mappings
- naming conventions
- method signatures
- file and project layout examples
- target-language syntax for loops, conditionals, and error handling

Read:
- `references/python-guidance.md` for Python conversions
- `references/csharp-guidance.md` for C# conversions

If the VI uses more than the basic arithmetic, string, array, and control-flow patterns covered by the selected language guide, also read `references/code-mappings.md` for extended built-in node mappings, NI driver/library mappings, and advanced construct handling.

### Step 4 — Map LabVIEW constructs to code patterns

#### Controls & Indicators → Method parameters and return values

Every `<Control>` becomes a parameter of the class method. Every `<Indicator>` becomes a return value. This applies to the top-level VI's primary method and to every recursively converted SubVI helper.

Use the selected target-language guide for exact parameter naming, default-value handling, return packaging, and method naming.

#### Error clusters → Exception handling

Map LabVIEW's `error in` / `error out` chain into the target language's exception or explicit-result pattern. Use the selected target-language guide for syntax and structure.

#### While Loop + Condition → while loop

Map this to the target language's native loop construct with an explicit stop or continue condition.

#### For Loop → for loop

Map this to a counted loop in the target language.

#### For Loop with auto-indexing tunnel → iteration over array

Map this to iteration over the source collection.

#### Shift Register → loop-carried variable

Map this to a loop-carried variable that is initialized once and updated on each iteration.

#### Case Structure → if/else or match

Map this to the target language's native conditional or switch/match construct.

#### Tunnel In/Out → variable scoping across structures

Tunnels just move data across structure boundaries. In text code, this is simply variable scoping — the variable defined outside the loop is accessible inside, and vice versa if assigned.

#### Index mode tunnels → auto-indexed iteration or array building

Map indexing input tunnels to collection iteration and indexing output tunnels to collection building.

#### Detailed node and library mappings

Read `references/code-mappings.md` when the diagram uses built-in nodes beyond the examples above, when a `<Call>` targets an NI library, or when the VI contains advanced constructs such as event structures, producer/consumer patterns, property nodes, or hardware APIs.

#### SubVI calls (`<Call>` elements)

- **NI driver SubVIs** — If the SubVI belongs to a known NI instrument driver, read `references/code-mappings.md` and map it to the equivalent API call in the target language.
- **Custom user SubVIs** — If the SubVI is a custom user VI in the project, **recursively extract its XML** using `get_vi_xml.py` and convert it to a method on the generated class. Do not create stubs — always extract and convert the full logic. Each SubVI becomes a method whose Controls are parameters and whose Indicators are return values.
- **Polymorphic SubVIs** — Use the `instance` attribute to determine the specific variant and pick the matching overload or generic method.
- **Recursive extraction rule** — When a SubVI itself calls other SubVIs, continue recursing until all custom VIs are converted. NI driver/library calls are the recursion boundary — they map to library APIs, not further extraction.

### Step 5 — Determine execution order

LabVIEW executes nodes based on data dependencies, not source order. To produce sequential code:

1. Build a dependency graph from the wire connections
2. Perform a topological sort
3. Nodes with no data dependency between them can appear in any order — group related operations together for readability
4. The error chain (`error in` → `error out`) often defines the intended sequential order; follow it when present

### Step 6 — Generate the code

The generated code must mirror the VI's structure as a **single class** with methods corresponding to the top-level VI and each SubVI. The class is instantiated and called from a `main` entry point.

#### Code structure rules

1. **One class per VI** — The top-level VI becomes a class. The class name is derived from the VI name (e.g., `MyAcquisition.vi` → `MyAcquisition`).
2. **Top-level VI → primary method** — The VI's block diagram logic becomes the class's primary method using the naming and casing conventions from the selected target-language guide.
3. **Controls → method parameters** — Each `<Control>` on the front panel becomes a parameter of the primary method, with its default value and naming derived using the selected target-language guide.
4. **Indicators → return values** — Each `<Indicator>` becomes a return value using the target language's preferred packaging strategy from the selected guide.
5. **SubVIs → helper methods or modules** — Each recursively extracted custom SubVI becomes a private helper or separate reusable unit according to the selected language guide and the project-level structure.
6. **Shared state** — If the VI uses globals, functional globals, or session handles (e.g., instrument driver sessions), store them as class instance attributes initialized in `__init__` / constructor.
7. **Entry point** — Use the target language's native entry-point pattern from the selected guide.

#### File layout examples

Read only the target-specific file-layout example that matches the chosen language:
- `references/python-guidance.md`
- `references/csharp-guidance.md`

#### Project-level output rules

When the source is a `.lvproj`, do not stop at a single translated file unless the user explicitly asks for that. Generate an output structure that matches how the original LabVIEW project is used.

For C# /.NET conversions:
- Create the solution and project structure before filling in translated code.
- Choose the target framework based on the installed SDK and templates available on the machine. Do not assume a specific framework version.
- Put reusable translated logic in a library project.
- Put the runnable demonstration, entry point, or smoke test in a small console or test project.
- Convert consumed `.ctl` typedef assets into explicit records, classes, or enums in the generated project instead of treating them as comments or unsupported files.
- Keep project-local XML, XSD, config, and sample data files available at runtime by copying or linking them into the generated project.

For Python conversions:
- Prefer a small package or module folder when converting more than one VI.
- Keep helper SubVIs in separate modules when that improves traceability.
- Convert consumed `.ctl` typedef assets into explicit dataclasses or enums in the generated package instead of leaving them implicit.
- Preserve sample data and schema files alongside the generated package when the translated code depends on them.

### Step 7 — Review and validate

After generating the code:

1. Walk through the VI XML and the generated code side-by-side to verify every node is accounted for
2. Check that every wire connection is represented (no dropped data paths)
3. Verify loop structures match (While → while, For → for, Case → if/switch)
4. Confirm shift registers are mapped to loop-carried variables correctly
5. Ensure error handling is present where the VI uses error clusters
6. Verify data types are consistent at each operation
7. Run the narrowest executable validation available for the generated output
8. If the first build or run fails, fix the local issue and rerun the same validation before expanding scope

**Executable validation guidance:**
- C# single file or project: run `dotnet build` on the generated project or solution, then run the smallest relevant `dotnet run` or test command.
- Python module or package: run the generated script, or execute a small behavior check that exercises the translated path.
- If runtime assets were copied or linked, verify the generated program can resolve them from its output directory.

Present the generated code to the user with a brief summary of:
- What the VI does
- Key design decisions made during translation
- List of SubVIs that were recursively converted (with their method names in the generated class)
- Any NI driver calls and which Python/C# library they map to
- Any LabVIEW-specific constructs that don't have a direct equivalent (e.g., front panel UI elements, property nodes)

### Step 8 — Create a conversion report

At the end of the conversion, create a Markdown report alongside the generated output, typically named `conversion-report.md`.

Use `assets/conversion-report-template.md` as the default starting point, then fill in the project-specific details.

The report must include:
- Source path that was converted (`.vi` or `.lvproj`)
- Target language and output location
- Validation commands that were run and whether they passed
- A VI-to-output mapping table showing where each VI ended up
- Any supporting files that were copied or linked into the output
- Any unresolved constructs, approximations, or manual follow-up needed

## Additional bundled resources

- `references/code-mappings.md` — extended built-in node mappings, NI driver/library mappings, and advanced construct handling.
- `references/python-guidance.md` — Python-only type mappings, naming rules, control-flow examples, and file layout guidance.
- `references/csharp-guidance.md` — C#-only type mappings, naming rules, control-flow examples, and file layout guidance.
- `assets/conversion-report-template.md` — default Markdown template for the final conversion report.

## Limitations

- **UI / Front Panel layout** cannot be translated. Only the block diagram logic is converted. If the VI has significant UI interaction (charts, graphs, buttons), note what UI framework the user should consider.
- **Timing-dependent behavior** (e.g., timed loops, hardware-timed acquisition) may not translate perfectly. Add comments noting where timing semantics differ.
- **Inline compiled nodes** (Formula Node, MathScript Node) contain text code already — extract and adapt it directly.
- **XNodes and custom primitives** may not have XML representations. Note them as stubs.

## File structure

```
labview-to-code/
├── SKILL.md                        ← You are here
├── assets/
│   └── conversion-report-template.md ← Default report template
├── labview_path.txt                ← LabVIEW executable path
├── references/
│   ├── csharp-guidance.md          ← C#-only output and naming guidance
│   ├── code-mappings.md            ← Extended node/library/construct mappings
│   ├── python-guidance.md          ← Python-only output and naming guidance
│   └── vixml-format-26.1.yml       ← VI XML format specification
├── scripts/
│   ├── get_vi_xml.py               ← Extract VI XML from a .vi file
│   ├── vi.py                       ← LabVIEW COM automation helper
│   └── GetVIXML.vi                 ← LabVIEW VI that performs XML export
```

## Prerequisites

- **LabVIEW** must be installed. The path in `labview_path.txt` must point to the correct `LabVIEW.exe`.
- **Python 3.10+** with `pywin32` installed (`pip install pywin32`).
- **Windows** — the extraction script uses COM automation which is Windows-only.
