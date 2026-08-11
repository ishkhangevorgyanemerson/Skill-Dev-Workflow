# Isolation Workflow

Use this workflow when the user needs a structured debug path instead of a single isolated hint.

## Goal

Shrink the problem space quickly and avoid blaming the DUT too early.

## Step 1 - Define The Symptom Precisely

Capture:

- failing metric
- where it fails
- whether it is stable or intermittent
- whether it is single-site, all-site, bench-only, or ATE-only
- whether the failure follows time, temperature, frequency, or code changes
- what **topic domain** it belongs to, such as gain, PAE, IL/ISO, P1dB, IP3, harmonic, ACP, EVM, DEVM, SEM, NF, S-parameters, switch time, waveform handling, DPD, TTR, DPAT, or external filter-box setup

If the user gives several wrong metrics, identify which one is the likely root symptom and which are downstream effects.

If the problem is really a chapter-specific flow rather than a generic measurement symptom, consult `topic-playbook.md` before deciding the debug order.

## Step 2 - Eliminate Pure Software Issues

Use the source-backed default:

- verify the sequence is internally valid
- if possible, run or reason through offline mode first
- validate step settings before touching hardware

Reason:

- the source material explicitly uses offline mode to remove software-only issues before hardware debug

## Step 3 - Reconfirm DUT Bring-Up

Check:

- required bias rails and supply pins
- digital control pattern correctness
- expected live voltages and currents
- expected DUT state before RF measurement

If the DUT is not in the expected state, deeper RF analysis is usually wasted effort.

## Step 4 - Validate Path, Calibration, And Loopback

Check:

- current calibration status
- cable loss correctness at the actual port and frequency
- switch path / routing correctness
- loopback behavior

Use this step aggressively whenever:

- power is wrong
- high-power behavior is suspicious
- multiple unrelated RF metrics are wrong
- one site behaves differently from the rest

## Step 5 - Align Timing To The Real Signal

Check:

- trigger delay
- measurement interval or sweep time
- burst duration
- duty cycle
- measurement offset and length
- digital pattern event timing

This is especially important for:

- bursty or TDD signals
- servo flows
- current measurements during RF on-time
- NR and WLAN EVM
- switch-time measurement

## Step 6 - Review Measurement-Specific Parameters

Examples:

- power or gain: reference level, offsets, servo settings
- ACP or ACLR: offset count, offset frequency, bandwidth
- EVM: slot/time offset, channel estimation, frequency error estimation, averaging
- SEM: offset-count logic, manual sweep time
- S-parameters: IFBW, port power, reference level, frequency list

Do not treat all RF failures as generic path problems. Once path and timing are clean, move to the metric-specific configuration.

## Step 7 - Reframe Correlation Problems Correctly

If the complaint is "ATE does not match bench" or "production does not match lab," ask:

- same plane?
- same waveform definition?
- same measurement method?
- same trigger/timing behavior?
- same thermal exposure?
- same offset strategy?
- golden DUT or KGU data available?

Many correlation gaps disappear once the comparison basis becomes fair.

## Step 8 - Check Production-Specific Failure Modes

For production issues, explicitly inspect:

- one-site-only vs all-site behavior
- multi-site synchronization options
- handler/socket/setup changes
- bulk correlation behavior
- FPY trend
- long-run software stability and resource cleanup

This prevents applying bench-debug logic to production-only problems.

## Step 9 - Escalate To DUT Root Cause Only After Upstream Layers Are Clean

Only after the above layers are reasonably cleared should you prioritize:

- real DUT gain shift
- compression behavior
- thermal sensitivity
- process variation
- device control or silicon behavior

## Suggested Output Style

When using this workflow for a user, produce:

1. A short framing statement naming the likely failure layer.
2. A short missing-info list.
3. Three to five prioritized checks.
4. For each check, the expected observation and the branch logic.
5. A compact note tying the recommendation back to source-backed patterns.
