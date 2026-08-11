# Knowledge Indexing Guidelines

This file defines how to maintain `knowledge-curated/index.json`.

## Index Record Schema

Each `records[]` entry should use:

```json
{
  "id": "2026-08-11_stl_session-cleanup-pattern",
  "title": "Deterministic STL session cleanup pattern",
  "path": "knowledge-curated/2026-08-11_stl_session-cleanup-pattern.md",
  "status": "approved",
  "skills": ["semiconductor-test-library-assistant"],
  "domains": ["stl", "instrument-lifecycle"],
  "languages": ["csharp", "python"],
  "tags": ["cleanup", "error-handling", "session-management"],
  "reviewed_by": "curator-name",
  "updated_at": "2026-08-11"
}
```

## Update Rules

1. Add entries only for approved curated records.
2. Use stable IDs with date + topic slug.
3. Keep `skills`, `domains`, and `tags` explicit to support routing.
4. Update `last_updated` on each index change.
5. Remove or mark stale records when guidance becomes obsolete.

