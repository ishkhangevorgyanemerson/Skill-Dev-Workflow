# Library Architecture Patterns

Use this structure for semiconductor test library code in both Python and C#.

## Recommended Layers

1. **Request/Config Model**
   - Typed fields for all required inputs
   - Validation at object creation or explicit `validate()` entry point

2. **Orchestrator**
   - Coordinates setup -> configure -> execute -> fetch -> verify -> cleanup
   - No hidden global state

3. **Instrument Adapters**
   - Thin wrappers around driver calls
   - Isolate driver details from test intent logic

4. **Result Model**
   - Typed result object with measurements, limits, verdict, and metadata

## Execution Phase Contract

Each test flow should keep these explicit phases:

1. `setup`: create/open sessions and initialize state
2. `configure`: apply deterministic settings from validated parameters
3. `execute`: arm/start/acquire
4. `fetch`: retrieve raw and derived metrics
5. `verify`: compare against limits and compute verdict
6. `cleanup`: close or dispose sessions in all cases

## Cross-Language Parity

When implementing in both languages:
- Keep function/class intent and parameter semantics equivalent
- Keep log events semantically aligned (open, configure, execute, fetch, verify, cleanup)
- Keep error messages similarly actionable

