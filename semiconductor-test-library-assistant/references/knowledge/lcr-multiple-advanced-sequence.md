# LCR Multiple Advanced Sequence Selection

## Applies To
- Skill: `semiconductor-test-library-assistant`
- Domains/tags: `stl`, `dcpower`, `lcr`, `advanced-sequencing`
- Languages: `csharp`

## Pattern Summary
- Configure multiple LCR advanced sequences in one session, then select one by name as the active sequence at run time.

## Recommended Action Pattern
1. Validate sequence names, selected target sequence, and step-input mode.
2. Build each sequence deterministically and store expected fetch count per sequence.
3. Set `ActiveAdvancedSequence`, run/initiate, fetch using selected sequence point count, then always abort/delete/reset.

## Validation Cues
- Two named sequences are created successfully.
- Selected sequence determines fetch point count and result length.
- No stale advanced sequence state remains after cleanup/reset.

## Caveats
- Bias step/count mismatch causes wrong fetch sizing or runtime errors.
- Multisite offset handling must be explicit and validated.
- Cleanup is mandatory to avoid cross-test contamination.

## Canonical Source
- Curated record path: `team-knowledge/knowledge-curated/2026-08-11_stl_lcr-multiple-advanced-sequence.md`
- Record ID: `2026-08-11_stl_lcr-multiple-advanced-sequence`

