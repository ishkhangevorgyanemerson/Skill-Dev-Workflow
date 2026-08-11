# Team Submission Ingestion Runbook

Use this runbook when a teammate sends a filled submission template and you want to publish it as knowledge for one or more skills.

## Inputs
- A filled submission in `knowledge-submissions/`
- Curation criteria in `curation-checklist.md`
- Routing metadata requirements in `knowledge-curated/index.json`

## Step 1: Store Raw Submission
1. Save file in `knowledge-submissions/`.
2. Rename to:
   - `YYYY-MM-DD_<topic>_<author>.md`

## Step 2: Curate
1. Open the submission.
2. Apply checks from `curation-checklist.md`.
3. Mark outcome:
   - Approved
   - Needs Revision
   - Rejected

Only continue if Approved.

## Step 3: Normalize into Curated Record
1. Create a new file in `knowledge-curated/` using:
   - `templates/curated-record-template.md`
2. Keep only reusable content:
   - Problem pattern
   - Resolution pattern
   - Validation pattern
   - Caveats and boundaries

## Step 4: Map to Target Skill(s)
Choose one or more skills in the record metadata, for example:
- `hardware-assistant`
- `semiconductor-test-library-assistant`

Add explicit tags:
- `domains`
- `languages`
- `tags`

## Step 5: Register in Index
1. Add record metadata to `knowledge-curated/index.json`.
2. Update `last_updated`.
3. Set record `status` to `approved`.

## Step 6: Publish Skill-Specific Extracts
For each tagged skill:
1. Create/update an entry in `<skill>/references/knowledge/` using:
   - `templates/skill-knowledge-entry-template.md`
2. Keep it concise and context-specific.
3. Add canonical reference path to the curated record.

## Step 7: Verify
1. Confirm skill `SKILL.md` routes to `references/knowledge/README.md`.
2. Run one representative prompt and confirm the response uses the new knowledge pattern.
3. If result is weak, improve extracted entry wording (not the canonical truth) first.

## Conflict Handling
- If two records conflict:
  - Keep latest approved as primary
  - Mark older one stale in index metadata
  - Add note explaining supersession

