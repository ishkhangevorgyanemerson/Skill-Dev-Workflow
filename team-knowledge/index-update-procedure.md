# Index Update Procedure

This procedure defines how to update `knowledge-curated/index.json` after approving a record.

## File
- `team-knowledge/knowledge-curated/index.json`

## Required Fields per Record
- `id`
- `title`
- `path`
- `status` (`approved`, `stale`, or `deprecated`)
- `skills` (array)
- `domains` (array)
- `languages` (array)
- `tags` (array)
- `reviewed_by`
- `updated_at` (`YYYY-MM-DD`)

## Steps
1. Confirm curated file exists under `knowledge-curated/`.
2. Add a `records[]` entry with complete metadata.
3. Update top-level `last_updated`.
4. Validate that every skill listed in `skills` exists in `skills/`.
5. If superseding an old record:
   - mark old record as `stale`
   - add a clarifying note to old/new record files

## Minimal Example Entry
```json
{
  "id": "2026-08-11_hw_unstable-voltage-after-fixture-change",
  "title": "Unstable voltage after fixture replacement",
  "path": "knowledge-curated/2026-08-11_hw_unstable-voltage-after-fixture-change.md",
  "status": "approved",
  "skills": ["hardware-assistant"],
  "domains": ["hardware-debug", "fixture"],
  "languages": [],
  "tags": ["voltage-instability", "fixture-change", "triage"],
  "reviewed_by": "curator-name",
  "updated_at": "2026-08-11"
}
```

