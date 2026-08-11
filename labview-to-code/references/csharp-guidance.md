# C# Conversion Guidance

Read this file only when the user chose C# as the target language. Do not read the Python guide unless the user explicitly wants a comparison or dual-language output.

## Type mappings

| LabVIEW Type | C# |
|---|---|
| `bool` | `bool` |
| `int8`, `int16`, `int32` | `sbyte`, `short`, `int` |
| `uint8`, `uint16`, `uint32` | `byte`, `ushort`, `uint` |
| `int64`, `uint64` | `long`, `ulong` |
| `double`, `single` | `double`, `float` |
| `string` | `string` |
| `path` | `string` |
| `array{T}` | `T[]` or `List<T>` |
| `array.2{T}` | `T[,]` or `T[][]` |
| `cluster{...}` | `class` or `record` |
| `enum` / `uint16{A,B,C}` | `enum` |
| `waveform` | Custom class |
| `cluster{bool.status,int32.code,string.source}` | Exception handling (`try/catch`) or an explicit result/error type |

## Naming and signatures

- Class names: convert the VI name to `PascalCase`.
- Controls: convert `_name` to `camelCase` parameter names.
- Indicators: return a single value, tuple, `record`, or result type depending on the output shape.
- SubVIs: prefer private helpers such as `HelperSubVi(...)` unless a separate class is clearer for a project-level conversion.
- Strip parenthesized default hints from names and use the value as the default parameter when appropriate.

**Example skeleton:**

```csharp
// Source: MyVI.vi
// Description: <one-line summary>

public sealed class MyVi
{
    private object? _sharedState;

    public (double[] Data, double Mean) Run(double sampleRate = 1000.0, int numSamples = 100)
    {
        var data = HelperSubVi(sampleRate);
        return (data, numSamples);
    }

    private double[] HelperSubVi(double sampleRate)
    {
        return new[] { sampleRate };
    }

    public static void Main(string[] args)
    {
        var vi = new MyVi();
        Console.WriteLine(vi.Run());
    }
}
```

## Control flow and error handling patterns

Use idiomatic C# syntax while preserving LabVIEW execution semantics.

```csharp
try
{
    var result1 = StepOne(...);
    var result2 = StepTwo(result1, ...);
}
catch (Exception exception)
{
    HandleError(exception);
}

var iteration = 0;
while (true)
{
    iteration++;
    if (stopCondition)
    {
        break;
    }
}

for (var i = 0; i < n; i++)
{
    ...
}

foreach (var element in inputArray)
{
    ...
}

var accumulator = initialValue;
for (var i = 0; i < n; i++)
{
    accumulator = SomeOperation(accumulator, ...);
}

if (selector)
{
    ...
}
else
{
    ...
}

switch (selector)
{
    case "option_1":
        ...
        break;
    default:
        ...
        break;
}

var results = new List<double>();
foreach (var element in array)
{
    results.Add(Transform(element));
}
```

## Project-level layout

- Single-VI conversion: a single `.cs` file can work for a small example.
- `.lvproj` conversion: prefer a solution with at least one library project and a small console or test host.
- Put reusable translated logic in library classes.
- Keep runtime XML/XSD/config/sample files available in the generated output by copying or linking them into the project.