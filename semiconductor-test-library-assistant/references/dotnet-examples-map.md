# .NET STL Examples Reference Map

Use this map when requests involve C# STL structure, API usage, lifecycle patterns, or step/module design.

Source repository:
`C:\Users\igevorgy\Desktop\STL\semi-test-library-dotnet-main`

## 1) STL Architecture and Coding Workflow

- `docs/UserGuide/Overview.md`
- `docs/UserGuide/WritingTestCode.md`
- `docs/UserGuide/InstrumentAbstraction.md`

Read these first when the user asks for high-level project structure, layering, or coding conventions.

## 2) Session Lifecycle, Setup/Cleanup, and Error Handling

- `docs/UserGuide/ConfiguringInstrumentSessions.md`
- `docs/UserGuide/ExceptionHandling.md`
- `SemiconductorTestLibrary.TestStandSteps/source/CleanupInstrumentation.cs`
- `SemiconductorTestLibrary.TestStandSteps/source/ResetInstrumentation.cs`

Use these when implementing safe initialization, deterministic cleanup, and explicit exception behavior.

## 3) Instrument API Pattern References (C#)

- `SemiconductorTestLibrary.Extensions/source/InstrumentAbstraction/DCPower/*.cs`
- `SemiconductorTestLibrary.Extensions/source/InstrumentAbstraction/DMM/*.cs`
- `SemiconductorTestLibrary.Extensions/source/InstrumentAbstraction/Digital/*.cs`
- `SemiconductorTestLibrary.Extensions/source/InstrumentAbstraction/DAQmx/*.cs`
- `SemiconductorTestLibrary.Extensions/source/InstrumentAbstraction/Relay/*.cs`

Use these for concrete API shapes, naming patterns, and extension-method style.

## 4) TestStand Step Structure and Reusable Steps

- `SemiconductorTestLibrary.TestStandSteps/source/*.cs`
- `docs/UserGuide/UsingTestStandSteps.md`
- `docs/UserGuide/advanced/CustomizingTestStandSteps.md`

Use these for step-oriented module patterns and standard input/output conventions.

## 5) End-to-End Examples and Snippets

- `Examples/source/CodeSnippets/**/*.cs`
- `Examples/source/TestPrograms/**/*.cs`
- `Examples/source/Sequence/**/*.cs`

Use these when the user wants practical templates or refactoring targets based on real workflows.

## 6) Advanced Topics

- `docs/UserGuide/advanced/BestPracticesForWritingExtensionMethodsInSTL.md`
- `docs/UserGuide/advanced/ExtendingTheSemiconductorTestLibrary.md`
- `docs/UserGuide/advanced/MakingLowLevelDriverCalls.md`
- `docs/UserGuide/advanced/ConcurrentCodeExecution.md`
- `docs/UserGuide/advanced/ParallelizationMethods.md`

Use these when requests involve extension design, low-level calls, or performance/concurrency tuning.

## Usage Rules

1. Prefer docs for intent and conventions; use code files to confirm concrete API signatures and patterns.
2. Keep generated/refactored code scoped to the user's requested language and behavior.
3. Do not copy large blocks verbatim from examples; adapt patterns to the user's requested interface.
4. Preserve this skill's scope: code authoring/refactoring/review only.

