# 📖 Workflow Guide

This section contains guides for all team members on how to participate in the AI Skill Development Workflow.

---

## For Team Members (Contributors)

### When should I contribute?
Contribute whenever you:
- Solve a bug or case related to STL, hardware, or general T&M
- Find an undocumented behavior or workaround
- Answer a customer question that required deep investigation

### How do I contribute?
1. Copy the appropriate template from [`05_Templates/`](../05_Templates/)
2. Fill in the template with your question, context, and solution
3. Save your file in [`01_Knowledge_Contributions/`](../01_Knowledge_Contributions/) under the correct category:
   - `STL/` — for Semiconductor Test Library issues
   - `Hardware/` — for hardware-specific topics
   - `General/` — for general test & measurement topics
4. Name the file descriptively, e.g., `ForceVoltage_HighCurrentLimit_Fix.md`
5. Either commit directly to the `contributions` branch or open a Pull Request

> 💡 **You do NOT need to build the skill yourself.** Your job is to document the problem and solution clearly. The skill owner will integrate it.

---

## For the Skill Owner (Team Lead)

### Responsibilities
- Monitor `01_Knowledge_Contributions/` and `03_Review_Queue/` regularly
- Review incoming contributions for clarity and correctness
- Integrate approved contributions into the appropriate skill in `02_Skills/`
- Archive processed contributions in `04_Archived/`
- Tag and version skills as they evolve

### Review Process
1. Check `03_Review_Queue/` for pending items
2. Validate technical accuracy of the contribution
3. Refactor into skill-compatible format (Q&A, reference code, explanation)
4. Add to the relevant skill's `knowledge_base/` folder
5. Move the original contribution to `04_Archived/`

---

## Naming Conventions

| Item | Format | Example |
|------|--------|---------|
| Contribution file | `Topic_Issue_Description.md` | `STL_ForceVoltage_NullRefError.md` |
| Skill version | `v<major>.<minor>` | `v1.2` |
| Archive file | `ARCHIVED_<original_name>` | `ARCHIVED_STL_ForceVoltage_NullRefError.md` |
