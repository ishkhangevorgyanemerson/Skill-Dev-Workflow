# Code Review Checklist

Apply this checklist before returning generated/refactored code.

## Critical

- [ ] All instrument sessions are closed/disposed in all execution paths
- [ ] No measurement-critical parameters are guessed silently
- [ ] No broad catch that swallows failures
- [ ] Pass/fail logic is explicit and unit-safe

## Warning

- [ ] Clear phase comments or structure (setup/configure/execute/fetch/verify/cleanup)
- [ ] Stable typed input and output models
- [ ] No magic numbers for limits, timing, or RF values
- [ ] Logging includes key lifecycle events and key parameter context

## Suggestion

- [ ] Duplicate logic extracted into shared helpers
- [ ] Naming improves readability across Python and C# parity
- [ ] Public API surface is small and focused

## Review Output Format

When reviewing existing code, report:
1. Severity
2. Finding
3. Why it matters
4. Concrete fix (with corrected code for Critical/Warning)

