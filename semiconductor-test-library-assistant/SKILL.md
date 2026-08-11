---
name: semiconductor-test-library-assistant
version: 1.0.0
description: Author and refactor semiconductor test library code in Python and C# with production-ready structure, parameter validation, logging, session lifecycle safety, and deterministic review checklists. Use this whenever the user asks for semiconductor test library implementation, cleanup, modernization, API design, or code review/refactor help, even if they do not explicitly say "library assistant."
---

# Semiconductor Test Library Assistant

## When to Use

Use this skill when the user needs help with semiconductor production-test library code, including:
- Creating new reusable test library modules
- Refactoring existing test library functions/classes
- Reviewing code quality, safety, and maintainability
- Standardizing Python and C# implementations to a common architecture

Use this skill only for code authoring/refactoring/review workflows.  
Do not use it for artifact conversion workflows like PinMap/STIL/TSRU transformations.

## Workflow

### Step 1 - Classify the Request

Classify on two axes before writing code:

1. **Task type**: new implementation, refactor, or review-only
2. **Language**: Python, C#, or both

If language is unspecified, ask the user.  
If both are needed, keep behavior and naming conventions aligned across both languages.

### Step 2 - Confirm Required Inputs

Before coding, verify the minimum required inputs:
- Measurement intent and pass/fail criteria
- Required instruments and key configuration parameters
- Expected function/class interface
- Required outputs (result object, logs, metadata, exceptions)

If a critical RF/measurement parameter is missing, ask the user instead of guessing.

### Step 3 - Build with Library-Grade Structure

Use [references/library-architecture.md](references/library-architecture.md) for structure.  
Implement code with:
- Explicit setup/configure/execute/fetch/verify/cleanup phases
- Shared parameter model (validated at boundaries)
- Clear, stable return types
- Consistent error propagation with context

### Step 4 - Apply Language Rules

Use [references/parameter-validation.md](references/parameter-validation.md) and follow:

- **Python**: type hints, dataclasses/typed config models, explicit context-manager or `try/finally` cleanup
- **C#**: strongly typed options/result classes, `using`/`try/finally` lifecycle control, explicit exception context
- Keep naming and behavior equivalent between languages unless the user requests divergence

### Step 4b - Use .NET STL Examples for C# Grounding

When the request is C#-heavy or asks about STL library structure/API usage, consult:
- [references/dotnet-examples-map.md](references/dotnet-examples-map.md)

Use that map to select the smallest relevant source/doc subset before generating code.

### Step 4c - Reuse Curated Team Knowledge

When a request resembles previously solved team cases, consult:
- [references/knowledge/README.md](references/knowledge/README.md)

Prefer curated knowledge patterns for:
- Known STL API pitfalls
- Repeated hardware/session lifecycle issues
- Reusable implementation and refactor patterns

If a curated pattern conflicts with explicit user requirements, follow user requirements and explain the tradeoff.

### Step 5 - Self-Review Before Returning

Run the checklist in [references/code-review-checklist.md](references/code-review-checklist.md).  
Fix critical and warning issues before presenting final code.

## Output Contract

When producing code, return:
1. A concise summary of what was implemented/refactored
2. The final code
3. Any required follow-up assumptions/questions

For review-only requests, return:
- Numbered findings with severity: Critical / Warning / Suggestion
- Corrected code for any Critical/Warning findings

## Critical Rules

1. Never silently assume measurement-critical values.
2. Never skip deterministic session cleanup.
3. Do not hide failures with broad catch-and-continue patterns.
4. Keep behavior deterministic and test-library oriented (no ad hoc script style).
5. Keep this skill scoped to code authoring/refactoring/review, not file-format conversion.
