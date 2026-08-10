# 🧪 STL Skill — Semiconductor Test Library Assistant

## Description
This AI skill answers questions and provides guidance related to the **NI Semiconductor Test Library (STL)** for .NET/TestStand.

**Primary Source Reference:** https://github.com/ni/semi-test-library-dotnet/tree/main

## Scope
- TestStand step usage (e.g., `ForceVoltageMeasureCurrent`, `MeasureVoltage`, etc.)
- Pin map configuration and TSM context setup
- Instrument session management
- Common errors and their solutions
- Code examples and best practices

## Out of Scope
- General LabVIEW (use `General_Skill`)
- Hardware calibration (use `Hardware_Skill`)

## Current Version
`v1.1` — Prioritizes the official STL GitHub repository as the first reference

## Usage
Point your AI assistant (e.g., GitHub Copilot, custom GPT, or NI's internal tool) to the `knowledge_base/` folder as context and configure the skill to check the official STL repository first before using fallback knowledge.

## Reference Priority
1. Official STL repository: https://github.com/ni/semi-test-library-dotnet/tree/main
2. Curated entries in [`knowledge_base/`](./knowledge_base/)
3. General STL/TestStand knowledge when the first two do not answer the question

## Knowledge Base
See the [`knowledge_base/`](./knowledge_base/) folder for all curated Q&A entries.
