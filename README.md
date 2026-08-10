# 🤖 AI Skill Development Workflow — Semiconductor Application Engineering

Welcome to the central repository for developing and managing AI skills within the Semiconductor Application Engineering team at National Instruments.

## 📌 Purpose

This repository provides a structured workflow for:
- Team members to **contribute knowledge** (Q&A, solutions, documentation)
- The **skill owner** (team lead) to build and maintain AI skills
- Monitoring, reviewing, and evolving skills over time

---

## 📁 Repository Structure

```
Skill-Dev-Workflow/
│
├── 00_Workflow_Guide/           # How-to guides for the team
├── 01_Knowledge_Contributions/  # Raw input from team members
│   ├── STL/                     # Semiconductor Test Library topics
│   ├── Hardware/                # Hardware-specific knowledge
│   └── General/                 # General test & measurement topics
│
├── 02_Skills/                   # Built AI skills (maintained by skill owner)
│   ├── STL_Skill/               # Skill: Semiconductor Test Library Q&A
│   ├── Hardware_Skill/          # Skill: Hardware troubleshooting
│   └── General_Skill/           # Skill: General T&M support
│
├── 03_Review_Queue/             # Contributions pending review by skill owner
├── 04_Archived/                 # Outdated or superseded contributions
└── 05_Templates/                # Templates for contributions and skills
```

---

## 🔄 Workflow Summary

| Step | Who | Action |
|------|-----|--------|
| 1 | Team member | Solves a problem → fills out contribution template |
| 2 | Team member | Opens a PR or drops file in `01_Knowledge_Contributions/` |
| 3 | Skill owner | Reviews in `03_Review_Queue/` |
| 4 | Skill owner | Builds/updates skill in `02_Skills/` |
| 5 | Skill owner | Archives or keeps contributions for traceability |

---

## 👥 Roles

- **Skill Owner (Team Lead)**: Reviews contributions, builds and maintains skills, monitors quality
- **Contributor (Team Member)**: Documents problems and solutions using the provided templates