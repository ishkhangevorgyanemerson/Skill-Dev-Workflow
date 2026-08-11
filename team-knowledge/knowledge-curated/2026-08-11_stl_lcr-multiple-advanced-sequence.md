# Curated Knowledge Record

## 1) Record Metadata
- Record ID: `2026-08-11_stl_lcr-multiple-advanced-sequence`
- Source submission file: `team-knowledge/knowledge-submissions/LCR_Multiple_Advanced_Sequence.md`
- Curator: Copilot CLI Assistant
- Review date: 2026-08-11
- Status: approved
- Target skills: `semiconductor-test-library-assistant`
- Domains: `stl`, `dcpower`, `lcr`, `advanced-sequencing`
- Languages: `csharp`
- Tags: `multiple-advanced-sequence`, `active-sequence-selection`, `fetch-points-by-sequence`, `sequence-cleanup`

## 2) Problem Pattern
- User needs a .NET STL pattern to configure multiple NI-DCPower LCR advanced sequences in one setup and run only the selected sequence safely.

## 3) Context Pattern
- NI Semiconductor Test Library usage with PXIe-4190.
- LCR mode with advanced sequencing and DC bias sweeps.
- Requirement to switch active sequence by name without rebuilding the whole flow.

## 4) Resolution Pattern
1. Validate sequence names, selected sequence, and bias-input mode (explicit list vs start/stop/step).
2. Build each advanced sequence with `CreateAdvancedSequence(...)` + `CreateAdvancedSequenceStep(...)` and set `LCR.DCBiasVoltageLevel` per step.
3. Track points-to-fetch per sequence, set `ActiveAdvancedSequence` to requested one, initiate, wait for source complete, fetch matching count, then abort/delete sequences/reset.

## 5) Validation Pattern
- Verify both sequences are created and visible before run.
- Verify selected sequence controls fetch length (`pointsToFetch` from selected sequence map).
- Verify measurement returns expected point count and no residual sequence state remains after delete/reset.

## 6) Reuse Boundaries
- Use when: one test step must prepare multiple LCR advanced sequences and choose one at execution time.
- Do not use when: only a single sequence is needed or sequence selection must happen across different sessions/resources.

## 7) Risks and Caveats
- Ensure step-count math and bias arrays are consistent; mismatches cause wrong point count or runtime errors.
- Always delete created sequences and reset session to avoid cross-test contamination.
- Treat site-based offset logic carefully in multisite scenarios.

## 8) Canonical References
- Internal docs: `semi-test-library-dotnet-main` STL examples and docs.
- Code references: submission code in `LCR_Multiple_Advanced_Sequence.md`.
- Vendor references: NI STL / NI-DCPower advanced sequencing API docs.

