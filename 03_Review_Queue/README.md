# 🔍 Review Queue

This folder is the **inbox for the Skill Owner**. Team members may place contributions here when they are not sure which category applies, or when they want explicit review before the file is added to the knowledge base.

## Process

1. Contributor drops a file here (or opens a PR targeting this folder)
2. Skill Owner reviews the file within **5 business days**
3. Skill Owner either:
   - ✅ Approves → moves to `01_Knowledge_Contributions/<category>/` and integrates into `02_Skills/`
   - ✏️ Requests changes → comments on the PR or adds a `FEEDBACK_` prefixed file
   - ❌ Rejects → moves to `04_Archived/` with a note explaining why

## Status Labels (for PR reviews)
- `pending-review` — awaiting skill owner review
- `approved` — accepted, being integrated
- `needs-update` — contributor action required
- `archived` — closed without integration
