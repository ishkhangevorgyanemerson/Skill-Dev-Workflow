# Symptom Taxonomy

Use this reference when the user gives a specific symptom. Start with the symptom family, then work through the fastest isolation checks.

If the user's question is mainly about a chapter-specific workflow such as IL/ISO, P1dB, IP3, Harmonic, DPD, TTR, DPAT, waveform loading, or PAMiD filter-box setup, also read `topic-playbook.md` so you do not collapse a domain-specific problem into a generic symptom answer.

## Power Or Gain Does Not Match

Typical user reports:

- "Power is too low/high"
- "Gain is larger than bench"
- "Max Pout does not line up with Max Icc"

Most likely layers:

1. Cable loss / calibration
2. Wrong measurement window
3. Thermal difference between ATE and bench
4. Wrong reference level / offsets / path settings

First checks:

1. Re-run loopback and verify cable loss at the real frequency/path.
2. Inspect trigger delay and measurement interval so acquisition lands in the stable waveform region.
3. Compare bench thermal exposure vs fast ATE measurement.

Source notes:

- Reference Solution, p.15-16
- RF FEM APT Test Manual, p.15-17

## Servo Failure Or Boundary-Pinned Result

Typical user reports:

- "Servo is far from target"
- "Servo pin is fixed at a boundary"
- "Vramp stays at endVoltage"

Most likely layers:

1. Wrong estimated gain or too-narrow gain window
2. Sweep range too small
3. Timing too short for the waveform style
4. Batch-to-batch variation larger than servo settings assume

First checks:

1. Measure DUT gain without servo and compare against estimated gain.
2. Check whether `Estimated Gain +/- Gain Accuracy` can cover actual DUT variation.
3. If Vramp servo is used, widen the voltage range and, if needed, increase step count.
4. Inspect servo traces or iteration count. If it takes the maximum steps and still misses target, treat it as failed servo.

Source notes:

- Reference Solution, p.16-17
- RF FEM APT Test Manual, p.17-24

## PAE Or Current Mismatch

Typical user reports:

- "PAE formula does not match published result"
- "Icc is too small"
- "Icc and power are both wrong and move together"

Most likely layers:

1. Correlation-offset handling
2. DC measurement timing
3. Calibration / thermal interaction

First checks:

1. If correlation offset is used, do not trust direct fetched PAE without applying the offset before calculation.
2. Align DC source delay and aperture so current is measured while RF is on and stable.
3. If current and power shift together, revisit calibration and heat impact.

Source notes:

- Reference Solution, p.17-18

## Bench-Vs-ATE Correlation Gap

Typical user reports:

- "Bench and ATE disagree"
- "Client lab data does not correlate"

Most likely layers:

1. Different measurement plane
2. Different waveform length or settings
3. Thermal mismatch
4. Invalid calibration or cable loss
5. Missing golden-unit correlation workflow

First checks:

1. Verify the same plane.
2. Verify the same settings and waveform definition.
3. Compare DUT thermal history.
4. Confirm calibration validity and path loss accuracy.
5. Use golden DUT / KGU flow where relevant.

Source notes:

- Reference Solution, p.10-14
- RF FEM APT Test Manual, p.16, p.78-81

## EVM Looks Bad Or Inconsistent

Typical user reports:

- "EVM is bad only on ATE"
- "Servo EVM is worse than non-servo EVM"
- "TDD waveform EVM is wrong"
- "WLAN EVM is unstable"

Most likely layers:

1. Waveform offset / length misalignment
2. Trigger-delay misalignment
3. Shared LO / noise-compensation / averaging differences
4. Channel estimation or frequency-error estimation settings

First checks:

1. Run loopback first to validate waveform and EVM setup.
2. For NR with nonzero start slot, align measurement offset or SA trigger delay to the actual waveform start.
3. For WLAN, inspect measurement offset/length and symbol-level EVM plots.
4. Compare channel-estimation and frequency-error-estimation settings against the customer's bench setup.

Source notes:

- RF FEM APT Test Manual, p.78-81

## ACP / ACLR Does Not Match

Typical user reports:

- "ACLR is wrong"
- "ACP is asymmetric"
- "NR UTRA results do not look right"

Most likely layers:

1. Wrong offset count or offset definition
2. Wrong offset frequency or integration bandwidth
3. Path asymmetry or attenuator mismatch

First checks:

1. Verify the number of offsets actually used by the protocol and test.
2. Verify offset frequencies and bandwidths.
3. If asymmetry exists, inspect attenuator and path matching.

Source notes:

- RF FEM APT Test Manual, p.68-71

## IL / ISO Or PAVT Segments Look Wrong

Typical user reports:

- "Segment power looks wrong"
- "IL/ISO result is unstable"
- "PAVT segments do not line up"

Most likely layers:

1. Pattern timing not matching SA segment timing
2. Segment count / start time mismatch
3. Publish Data ID interpretation mistake

First checks:

1. Verify segment length is identical in the pattern and SA configuration.
2. Verify `event0`, segment start, interval, measurement offset, and total length all align.
3. Use RFmx SFP at a breakpoint to inspect the segmented behavior.

Source notes:

- RF FEM APT Test Manual, p.34-41

## P1dB Or Compression Result Is Missing Or Wrong

Typical user reports:

- "Cannot get P1dB"
- "Compression point is clearly wrong"

Most likely layers:

1. Ramp waveform dynamic range too small
2. Wrong AMPM waveform assumptions
3. Measurement never reaches saturation

First checks:

1. Confirm the waveform is a valid ramp / triangle waveform for AMPM use.
2. Estimate whether the waveform PAPR and dynamic range can actually reach the DUT compression region.
3. If not, regenerate the waveform with larger dynamic range.

Source notes:

- Reference Solution, p.18
- RF FEM APT Test Manual, p.42-46

## IP3 / IM3 Result Is Wrong

Typical user reports:

- "IP3 is off by about 3 dB"
- "Instrument IM3 is interfering"

Most likely layers:

1. Total-vs-per-tone power misunderstanding
2. VST-generated IM3 contamination
3. Manual sanity-check not yet done

First checks:

1. Confirm configured power is total two-tone power.
2. Increase reference level or adjust SG settings if instrument IM3 is suspected.
3. Use manual OIP3 evaluation in the soft panel if needed.

Source notes:

- Reference Solution, p.18-19
- RF FEM APT Test Manual, p.47-52

## Harmonic Result Is Too High Or Calibration Looks Wrong

Typical user reports:

- "Harmonic is higher than bench"
- "HMU calibration is failing"
- "Sub8 harmonic result is unstable"

Most likely layers:

1. Fundamental leakage / filtering problem
2. Missing external filter or coupler strategy
3. Wrong HMU / 5831 calibration setup
4. Shared LO or path configuration mismatch

First checks:

1. Check whether the setup sufficiently separates the fundamental from the harmonic.
2. For HMU / 5831 flows, verify TDMS and S2P calibration files and the exact frequency coverage.
3. Confirm SG/SA LO-sharing behavior matches the harmonic method.

Source notes:

- Reference Solution, p.19
- RF FEM APT Test Manual, p.53-65

## SEM Is Wrong Or Unstable

Typical user reports:

- "SEM margin is inaccurate"
- "SEM fluctuates too much"

Most likely layers:

1. Offset-count logic
2. Auto sweep-time choice too short
3. Measurement-path settings

First checks:

1. Verify how many offsets the code is actually evaluating.
2. Replace auto sweep time with a manual, longer sweep and compare stability.

Source notes:

- RF FEM APT Test Manual, p.82-84

## S-Parameter Or User-Defined Calibration Failure

Typical user reports:

- "Calibration fails at one frequency"
- "S-parameter result naming or settings are confusing"

Most likely layers:

1. Sweep settings not matched to the real need
2. Calibration hardware issue such as CLB
3. Publish-ID customization confusion rather than measurement failure

First checks:

1. Review `portPower`, `referenceLevel`, IFBW, and real frequency list.
2. If calibration fails only at a specific point, suspect CLB and retry with replacement hardware.

Source notes:

- RF FEM APT Test Manual, p.100-101

## Switch-Time Or Trigger Sequencing Failure

Typical user reports:

- "Switch time result is wrong"
- "The waveform capture does not align with the state transition"

Most likely layers:

1. Pattern event order
2. Insufficient wait time between RFSG and RFmx events
3. DUT control sequence mismatch

First checks:

1. Inspect the pattern timeline: event0 for RFSG, DUT switch event, event1 for RFmx capture.
2. Verify that acquisition windows map to the expected state transitions.

Source notes:

- RF FEM APT Test Manual, p.103+

## One Site Fails, Or Production Yield Drops

Typical user reports:

- "Only one site fails"
- "Parallel test behaves differently"
- "FPY dropped in production"

Most likely layers:

1. Site-specific pin map / calibration / hardware path issue
2. Multi-site execution or synchronization configuration
3. Handler/socket/setup issue
4. Correlation offset not updated for production state

First checks:

1. Compare failing site vs passing site with the same DUT family.
2. Review pin map, calibration file, and hardware connections for that site.
3. Re-check Bin1 and runtime behavior after multi-site enablement.

Source notes:

- Reference Solution, p.11-14

## Long-Run Runtime Or Memory Resource Failure

Typical user reports:

- "After many DUTs, memory resources are exhausted"
- "The test runs for a while, then becomes unstable"

Most likely layers:

1. Software leak
2. Resource cleanup bug
3. Production-only endurance issue

First checks:

1. Reproduce after long runs rather than one-shot debug.
2. Use DETT or equivalent leak tracing.
3. Look for unclosed references or recently added callbacks/helpers.

Source notes:

- RF FEM APT Test Manual, p.139-142

## Throughput / TTR Is The Main Problem

Typical user reports:

- "Test time is too long"
- "Servo takes too many steps"
- "DC timing dominates total runtime"

Most likely layers:

1. Unoptimized servo timing
2. Excessive tracing or result processing
3. DC step timing too conservative
4. Waveforms or averages longer than needed

First checks:

1. Use Power Servo Trace Viewer or DCPower Trace Viewer to tune timing.
2. Disable unnecessary tracing and result processors.
3. Revisit DC aperture / settling assumptions and waveform duration.

Source notes:

- Reference Solution, p.12-13
- RF FEM APT Test Manual, p.132-142
