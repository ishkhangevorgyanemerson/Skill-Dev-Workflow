# Parameter Validation Conventions

Validate inputs before any instrument interaction.

## Required Categories

1. **Signal definition**
   - Frequency or channel definition
   - Standard/bandwidth where applicable

2. **Power/reference**
   - Input or expected power levels
   - Analyzer reference level or equivalent

3. **Resources**
   - Instrument resource names
   - Triggering mode/line when multi-instrument orchestration is used

4. **Limits**
   - Pass/fail thresholds with units

## Validation Rules

- Reject missing required fields with explicit errors.
- Reject out-of-range values with units in error messages.
- Normalize units once at boundary and use normalized values internally.
- Do not default critical RF values unless user explicitly approved defaults.

## Error Message Pattern

Use clear, actionable messages:
- What failed
- Which parameter caused it
- Expected range/format
- How to fix

Example:
`Invalid center_frequency_hz: -1.0. Expected value > 0 Hz.`

