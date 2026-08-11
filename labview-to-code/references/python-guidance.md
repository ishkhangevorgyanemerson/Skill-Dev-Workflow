# Python Conversion Guidance

Read this file only when the user chose Python as the target language. Do not read the C# guide unless the user explicitly wants a comparison or dual-language output.

## Type mappings

| LabVIEW Type | Python |
|---|---|
| `bool` | `bool` |
| `int8`, `int16`, `int32` | `int` |
| `uint8`, `uint16`, `uint32` | `int` |
| `int64`, `uint64` | `int` |
| `double`, `single` | `float` |
| `string` | `str` |
| `path` | `str` or `pathlib.Path` |
| `array{T}` | `list[T]` or `numpy.ndarray` |
| `array.2{T}` | `list[list[T]]` or 2D `numpy.ndarray` |
| `cluster{...}` | `dataclass` or `namedtuple` |
| `enum` / `uint16{A,B,C}` | `enum.Enum` |
| `waveform` | Custom class or dict |
| `cluster{bool.status,int32.code,string.source}` | Exception handling (`try/except`) or an explicit error dataclass |

## Naming and signatures

- Class names: convert the VI name to `PascalCase`.
- Controls: convert `_name` to `snake_case` parameter names.
- Indicators: return a single value, tuple, dataclass, or small result object depending on the number and meaning of outputs.
- SubVIs: prefer private helpers such as `_helper_subvi(...)` unless a separate module is clearer for a project-level conversion.
- Strip parenthesized default hints from names and use the value as the default argument when appropriate.

**Example skeleton:**

```python
# Source: MyVI.vi
# Description: <one-line summary>

from dataclasses import dataclass


@dataclass
class SomeCluster:
    field1: float
    field2: str


class MyVi:
    def __init__(self) -> None:
        self._shared_state = None

    def run(self, sample_rate: float = 1000.0, num_samples: int = 100) -> tuple[list[float], float]:
        result = self._helper_subvi(sample_rate)
        return result, float(num_samples)

    def _helper_subvi(self, sample_rate: float) -> list[float]:
        return [sample_rate]


if __name__ == "__main__":
    vi = MyVi()
    print(vi.run())
```

## Control flow and error handling patterns

Use idiomatic Python syntax while preserving LabVIEW execution semantics.

```python
try:
    result_1 = step_one(...)
    result_2 = step_two(result_1, ...)
except Exception as exc:
    handle_error(exc)

iteration = 0
while True:
    ...
    iteration += 1
    if stop_condition:
        break

for i in range(n):
    ...

for element in input_array:
    ...

accumulator = initial_value
for i in range(n):
    accumulator = some_operation(accumulator, ...)

if selector:
    ...
else:
    ...

match selector:
    case "option_1":
        ...
    case _:
        ...

results = []
for element in array:
    results.append(transform(element))
```

## Project-level layout

- Single-VI conversion: one `.py` file is acceptable if the helper surface is small.
- Multi-VI or `.lvproj` conversion: prefer a package or module folder.
- Keep helper SubVIs in separate modules when that improves traceability or reuse.
- Keep runtime XML/XSD/config/sample files adjacent to the generated package when the code depends on them.