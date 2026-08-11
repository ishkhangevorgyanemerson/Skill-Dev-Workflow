# RF Troubleshooting Summary

This note distills the two source PDFs into practical troubleshooting guidance. Page numbers below refer to the extracted source PDFs under `.try/troubleshooting/`.

## Source Documents

1. `Documentation for Semi RFIC Production Test Reference Solution.pdf`
2. `RF FEM APT Test Manual.pdf`

## Core Patterns From The Source Material

### 1. Remove software-only issues first

The reference solution explicitly recommends using **Offline Mode** and making sure the sequence runs without errors before instrument debugging.

- Source: Reference Solution, p.4-5
- Quote: "In Offline Mode, make sure that the sequence runs without errors to avoid any pure software issues."

Implication:

- If the user is seeing failures that may come from step configuration, sequencing, or general logic, first separate those from hardware-dependent problems.

### 2. Bring-up should confirm power, digital state, and path visibility before advanced RF debugging

The reference solution's bring-up flow emphasizes:

- identifying powered pins from datasheet, test plan, and schematics
- using Digital Pattern Editor to power up the DUT
- observing pin states, voltages, and currents in real time
- using the STS RF Switch Control Panel to check RF measurements

- Source: Reference Solution, p.6-8

Implication:

- When RF results look wrong, do not skip basic bring-up evidence. A surprising number of "RF issues" are actually power-up, digital control, or path-selection issues.

### 3. Bin1 debugging is a settings-and-tools problem before it is a theory problem

The reference solution recommends these tools for debugging failing steps and getting Bin1 pass:

- validate step settings
- STS RF Switch Control Panel
- NI I/O Trace
- RFmx Soft Front Panel

- Source: Reference Solution, p.9-10

Quote:

- "check the step settings and verify that each configuration is properly set"

Implication:

- When a user says a test step is failing, first inspect configuration correctness and live API behavior before proposing exotic RF root causes.

### 4. Correlation failures are often method mismatches, not DUT failures

The reference solution treats data correlation as a structured activity:

- get golden DUT data from OSAT or lab
- use the same measurement settings
- make sure you test to the same plane
- keep calibration valid and cable loss accurate

- Source: Reference Solution, p.10-14

Quotes:

- "use the golden DUT data as a reference"
- "Make sure that you are testing to the same plane"
- "Make sure that your test system calibration is valid, and the cable loss specified in your test sequence is accurate"

Implication:

- Bench-vs-ATE disagreements should first be framed as a correlation problem: same plane, same waveform, same settings, same thermal state, same offsets.

### 5. If many things are wrong, make power correct first

The RF FEM manual states a blunt heuristic: when results do not match, the first step is to make sure **power** is correct.

- Source: RF FEM APT Test Manual, p.15
- Quote: "所有测试结果对不上的情况下，第一步就是保证功率对的上"

Implication:

- If power is not trusted, derived metrics such as gain, PAE, ACLR, or EVM cannot be trusted either.

### 6. High-power mismatches often point to cable loss or loopback/calibration issues

When Max Pout does not match Max Icc, the documents recommend:

- compensate cable loss again
- perform loopback to confirm system components are calibrated

- Source: Reference Solution, p.15-16
- Source: RF FEM APT Test Manual, p.15

Implication:

- Near saturation, hardware path and loss accuracy should be cleared before blaming DUT compression behavior.

### 7. Bench-vs-ATE gain mismatches may be thermal, not wrong measurement

Both documents describe a common case: bench data is collected after the DUT has heated up, while ATE servo completes in milliseconds.

- Source: Reference Solution, p.16
- Source: RF FEM APT Test Manual, p.16-17

Key idea:

- ATE may read higher gain or need lower servo pin simply because the DUT has not thermally drooped yet.

Recommended handling:

- confirm the customer's actual bench scenario
- run a heat experiment on ATE
- capture power after several seconds and compare the delta

### 8. Servo failures have recognizable patterns

The sources call out strong servo failure signals:

- Pout noticeably different from target
- servo pin fixed at a boundary value after several loops
- Vramp equal to start/end voltage repeatedly
- too many servo iterations before error

- Source: Reference Solution, p.16-17
- Source: RF FEM APT Test Manual, p.17-24

Useful actions:

- compare real DUT gain with estimated gain
- widen gain accuracy or voltage range as needed
- increase step count if wider range hurts accuracy
- inspect servo traces or graphs when available

### 9. Timing windows matter for power, current, EVM, and switch-time results

The RF FEM manual repeatedly stresses alignment between:

- trigger delay
- measurement interval
- waveform length
- effective burst duration
- duty cycle
- digital trigger timing

- Source: RF FEM APT Test Manual, p.11-13, p.15-17, p.78-79, p.103+

Quotes and examples:

- For power: the acquisition region must land where the DUT output is stable and present.
- For NR EVM with `start slot != 0`: shift measurement offset or trigger delay to the actual start.
- For switch time: pattern construction and event timing are critical to capturing the right IQ segments.

Implication:

- Many RF failures are really time-alignment failures.

### 10. EVM correlation depends on waveform and algorithm choices

The RF FEM manual calls out these EVM-sensitive factors:

- waveform length and slot coverage
- shared LO
- noise compensation
- path optimization method
- vector averaging
- frequency-error estimation method
- channel estimation method
- measurement offset and length

- Source: RF FEM APT Test Manual, p.78-81

Especially important:

- Quote: "先 LOOPBACK 看结果，确认波形和 EVM 设置没问题再进行下一步"

Implication:

- Before looking for deep DUT distortion, validate waveform integrity and EVM configuration in loopback.

### 11. SEM instability may be a sweep-time problem

The manual recommends manually setting a longer sweep time instead of relying on SEM auto sweep time when results are inaccurate or unstable.

- Source: RF FEM APT Test Manual, p.83-84

Implication:

- If SEM is noisy or unstable, do not only chase hardware noise. Check acquisition settings.

### 12. Some calibration failures are hardware-side, not just software-side

For user-defined S-parameter calibration failures at a specific point, the manual explicitly suggests that the CLB may be the issue and should be replaced for retry.

- Source: RF FEM APT Test Manual, p.101

Implication:

- Treat isolated calibration-point failures as possible calibration-hardware problems, not only parameter mistakes.

### 13. Production debugging must think in sites, yield, and long-run behavior

The reference solution and manual add production-specific expectations:

- validate Bin1 again after enabling multi-site
- compare sequential vs parallel runtime
- use KGU / golden units for production correlation
- do bulk correlation and first-pass-yield validation
- investigate long-run memory errors with DETT

- Source: Reference Solution, p.11-14
- Source: RF FEM APT Test Manual, p.139-142

Implication:

- A production issue may not look like a bench issue. The debug model should include site effects, handler flow, offset updates, and long-run software stability.

## Tooling Called Out By The PDFs

- Offline Mode
- Digital Pattern Editor
- STS RF Switch Control Panel
- RFmx Soft Front Panel
- NI I/O Trace
- DCPower Trace Viewer
- Power Servo Trace Viewer
- ETW / I/O trace style servo trace methods
- DETT for leak analysis

## Bottom-Line Guidance

When helping a user debug RF results from these environments, the safest default order is:

1. Confirm the sequence and step settings are logically valid.
2. Confirm DUT bring-up, bias, and digital control.
3. Confirm calibration, cable loss, and loopback.
4. Confirm trigger, timing window, and waveform alignment.
5. Confirm measurement-specific parameters.
6. Confirm correlation plane, thermal conditions, and offsets.
7. Only then spend energy on deep DUT root cause.
