# Hardware Triage Workflow

Use this sequence for deterministic troubleshooting.

## 1) Confirm Symptom and Scope
- Exact failure symptom
- Affected scope (single unit/site/system-wide)
- Frequency (constant/intermittent/thermal/time-dependent)

## 2) Check Recent Changes
- Hardware swaps, cabling, fixtures
- Firmware/software updates
- Configuration or calibration changes

## 3) Isolate by Fault Class
- Power/supply path
- Connectivity and signal path
- Timing/trigger/synchronization
- Configuration/API misuse
- DUT or external environment factors

## 4) Run Minimal Verification Sequence

For each check:
1. Action
2. Expected good observation
3. Expected bad observation
4. Next branch decision

Start with fastest checks that eliminate whole fault classes.

## 5) Propose Corrective Action
- Immediate fix
- Confirmation re-test
- Monitoring criteria to prevent regression

## 6) Escalation Rule

Escalate when:
- Safety risk exists
- Critical context is missing and cannot be obtained
- Evidence is contradictory after standard checks

