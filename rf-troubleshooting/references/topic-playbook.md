# Complete Topic Playbook

This reference is intentionally broader than a symptom cheat sheet. It covers the full set of troubleshooting-oriented domains found in the two source PDFs, including measurement issues, production-debug workflows, infrastructure setup, and test-program diagnostics.

Use this file when the user's problem maps to a specific measurement domain or program topic.

## 1. System Overview And Core Debug Utilities

Use for:

- bring-up and basic STS debug
- sub8 InstrumentStudio workflows
- Publish Data ID customization
- general error-handling patterns

Key guidance:

- On sub8 systems, use InstrumentStudio-based panels rather than older standalone STS RF Debug Panel flows.
- Keep RFPM switch resource names aligned with Pin Map settings.
- Use the correct VST resource choice for the frequency range under debug.
- Open RFmx SFP early so you can see live behavior while debugging paths and waveforms.
- Only customize Publish Data IDs when TestStand-side expressions are not enough.
- Reuse proven error-handling patterns instead of inventing new ad hoc exception paths.

Source notes:

- RF FEM APT Test Manual, p.4-8

## 2. Gain / Power / Servo / Vramp Servo

Use for:

- fixed-Pin power tests
- Pout servo problems
- Vramp servo problems
- bench-vs-ATE gain mismatches

Main debugging levers:

- Confirm whether the issue is a fixed-Pin case, Pout servo case, or Vramp servo case.
- Re-check cable loss and loopback before debating DUT behavior.
- Align trigger delay and measurement interval to the stable-power part of the waveform.
- For bench-vs-ATE mismatch, compare thermal history and heat exposure.
- For servo failure, compare actual gain to estimated gain and inspect iteration count or traces.
- For Vramp servo hitting `endVoltage`, widen the sweep range and increase steps if needed.

Source notes:

- Reference Solution, p.15-17
- RF FEM APT Test Manual, p.9-29

## 3. PAE / Icc / DC Timing

Use for:

- PAE formula mismatch
- Icc too small
- Icc and power both wrong
- SMU-timing-related issues

Main debugging levers:

- If correlation offsets are used, apply them before calculating PAE.
- Ensure current is measured while RF is active and stable.
- Tune source delay and aperture time with DCPower traces if available.
- If current and power move together, suspect calibration or thermal causes, not just math.
- If DC response still looks wrong, inspect SMU transient-response configuration.

Source notes:

- Reference Solution, p.17-18
- RF FEM APT Test Manual, p.30-33

## 4. IL / ISO / PAVT Segment-Based Measurements

Use for:

- insertion loss or isolation via switch-state stepping
- PAVT power segmentation
- PAVT plus Icc combined debug

Main debugging levers:

- Keep pattern segment timing and SA segment timing exactly aligned.
- Ensure the pattern issues `event0` at the first segment and preserves segment interval consistency.
- Confirm `NumberOfSegments`, `Segment0StartTime`, offset, and length match the actual pattern.
- Use RFmx SFP during breakpoint-based debug to inspect segmented behavior visually.
- Watch for bundle-version differences in Publish Data IDs.
- If direct IL/Gain results are awkward to derive, a custom DLL may be justified.

Source notes:

- RF FEM APT Test Manual, p.34-41

## 5. P1dB / AMPM Ramp-Based Compression Tests

Use for:

- cannot get P1dB
- compression point clearly wrong
- ramp-waveform design issues

Main debugging levers:

- Use AMPM with ramp waveform; do not use servo in this measurement style.
- Make sure the ramp waveform dynamic range is large enough to reach compression.
- Use waveform PAPR plus estimated gain to estimate whether the scan enters saturation.
- If not, increase waveform dynamic range and regenerate the TDMS waveform.

Source notes:

- Reference Solution, p.18
- RF FEM APT Test Manual, p.42-46

## 6. IP3 / IM3

Use for:

- IP3 differs from bench by about 3 dB
- VST-generated IM3 interferes with measurement
- manual OIP3 evaluation questions

Main debugging levers:

- Confirm SG input power is the **total two-tone power**, not per-tone power.
- If instrument IM3 is the problem, consider self-cal or changing reference level / SG power / digital gain.
- Manual RFSG + RFSA soft-panel evaluation is useful for sanity checks.
- On platforms with two VSGs, ENDC-style two-source approaches may help.

Source notes:

- Reference Solution, p.18-19
- RF FEM APT Test Manual, p.47-52

## 7. Harmonic

Use for:

- sub6 harmonic issues
- >6 GHz harmonic with HMU SC2250
- >8.5 GHz harmonic with 5831
- harmonic filter-box or calibration issues

Main debugging levers:

- For sub6, choose TXP or CHP depending on CW vs modulated signal.
- Harmonic tests usually reuse servo power from a previous fundamental-power step.
- Disable shared LO when SG and SA frequencies differ.
- Use external filters/couplers when dynamic range is too large.
- For HMU / 5831 flows, debug both user-defined scalar calibration and cable-loss de-embedding.
- Include the slightly-above-maximum frequency point in HMU path-loss calibration when required.
- Verify that TDMS and S2P calibration files are bound correctly in Pin Map.

Source notes:

- Reference Solution, p.19
- RF FEM APT Test Manual, p.53-65

## 8. ACP / ACLR

Use for:

- wrong ACP or ACLR
- asymmetric ACP result
- 5G NR UTRA configuration issues
- bench mismatch for ACP

Main debugging levers:

- Verify offset count, offset frequency, and integration bandwidth.
- Distinguish protocol-defined offsets from custom SpecAn-style offsets.
- If left/right results are asymmetric, inspect path and attenuator matching.
- If bench mismatch persists, consider waveform optimization such as improved ACP filtering.
- If waveform edits cause trigger-delay problems, check burst-start properties rather than forcing a measurement explanation.

Source notes:

- Reference Solution, p.19
- RF FEM APT Test Manual, p.66-71

## 9. EVM

Use for:

- general ModAcc problems
- servo-vs-non-servo EVM mismatch
- data correlation for EVM
- NR start-slot issues
- WLAN EVM setting questions

Main debugging levers:

- If servo degrades EVM, separate servo and EVM into two steps.
- For correlation, compare waveform length, shared LO, noise compensation, optimization mode, and averaging strategy.
- For NR with nonzero start slot, align measurement offset or trigger delay to the real burst start.
- If EVM must coexist with other measurements and timing alignment still conflicts, consider trimming the waveform so the valid RF region starts at time zero.
- For WLAN, inspect measurement offset/length, frequency-error estimation, channel-estimation method, and averaging.
- Loopback is a preferred first debug move before blaming DUT modulation quality.

Source notes:

- Reference Solution, p.20
- RF FEM APT Test Manual, p.72-81

## 10. DEVM

Use for:

- WLAN burst-EVM / DEVM issues
- PA enable timing around burst waveforms

Main debugging levers:

- Treat DEVM as a burst-timed modulation test, not a generic EVM test.
- Enable pattern triggering and align PA enable timing to the RF arrival time.
- Check whether the sequence should enable PA before SG trigger or after, depending on waveform transport delay.
- Ensure burst-detection and max measurement interval fit the real burst length.

Source notes:

- RF FEM APT Test Manual, p.73-77

## 11. SEM

Use for:

- inaccurate SEM margins
- unstable SEM

Main debugging levers:

- Verify how many offsets are actually configured and measured.
- If auto sweep time is unstable, manually set a longer sweep time.

Source notes:

- Reference Solution, p.20-21
- RF FEM APT Test Manual, p.82-84

## 12. Noise Figure

Use for:

- NF affected by the environment
- cold-source calibration problems
- noisy or unstable NF setups

Main debugging levers:

- Use loopback and physical inspection to identify where interference enters.
- Consider shielding or moving the test frequency if the environment is the root cause.
- For VST-based use, choose the proper automatic setting to avoid configuration errors.
- Do not run cold-source calibration as part of every production test execution.
- During calibration, remove the DUT or at least power it down.
- Disconnect the SG path before NF test to reduce contamination.
- Make sure S21 or gain information feeding the cold-source flow is valid.
- Tune measurement bandwidth and interval as an accuracy-vs-time tradeoff.

Source notes:

- Reference Solution, p.21
- RF FEM APT Test Manual, p.85-93

## 13. S-Parameters / User-Defined Calibration

Use for:

- S-parameter instability
- user-defined calibration failures
- sweep-setting questions
- result-name customization

Main debugging levers:

- S-parameter measurement requires vector sweep settings and user-defined calibration.
- If using temporary calibration from another tester, inspect RF Initialize checks such as VST serial-number validation.
- Use sweep-setting names that only test required points when time matters.
- Tune IFBW based on accuracy vs time, then recalibrate.
- Review `portPower`, `referenceLevel`, and frequency list design.
- If calibration fails only at one point, suspect CLB hardware as well as file setup.
- If Publish Data IDs are error-prone, rename them in code intentionally and rebuild.

Source notes:

- Reference Solution, p.21
- RF FEM APT Test Manual, p.94-102

## 14. Switch Time

Use for:

- missing switch-time result
- flat IQ capture
- NaN switch-time values
- Golden Unit calibration questions
- custom rise/fall-only requirements

Main debugging levers:

- Pattern construction is critical: event0 for RFSG, event1 for RFmx capture, DUT on/off at the right points.
- Verify sample rate, acquisition time, pretrigger time, and record count.
- Use Golden Unit calibration when tester delay must be removed.
- If IQ is flat, inspect DUT state changes and acquisition placement before blaming the fetch math.
- Manually debug with Digital Pattern Editor, RF debug panels, and RFmx SFP.
- If needed, export raw IQ to CSV and analyze offline.
- For unusual rise/fall requirements or high-speed MIPI cases, source-code changes may be needed.

Source notes:

- Reference Solution, p.22
- RF FEM APT Test Manual, p.103-110

## 15. Waveform Creator / Waveform Loading

Use for:

- TDMS waveform generation questions
- load-waveform path/name errors
- 5841 vs 5646 loading differences

Main debugging levers:

- Generate TDMS waveforms before building automated flows.
- Keep waveform names simple and stable.
- Distinguish clearly between names without `.tdms` and file paths with `.tdms`.
- Be careful about different load semantics on different VST families.

Source notes:

- Reference Solution, p.4
- RF FEM APT Test Manual, p.111-112

## 16. WLAN DPD

Use for:

- DPD Trim / Measure debug
- DPD waveform database flow
- pre-stored waveform usage
- adapter error `-1074130544`

Main debugging levers:

- DPD is intended for nonlinear-region EVM improvement, not saturated-region testing.
- Production usually trims only a small number of DUTs per lot, then reuses those waveforms.
- If an adapter/runtime error exists, fix that first before debugging waveform reuse or trim-flow policy.
- Keep DPD Flow Signal Names and step-specific signal names consistent.
- Understand Trim Flow modes: first-DUT only, not-trim with pre-stored waveforms, trim-all, or input-flag-driven.
- `RF Load DPD Waveforms` is required when using saved or pre-generated DPD waveforms.
- Keep the default `postMpDpd` filter keyword when loading generated DPD files.
- If mixed C# DC code and LabVIEW RF code trigger error `-1074130544`, switch the LabVIEW adapter to Run-Time Engine mode.
- Use `SaveToFile` only for debug or waveform preparation, not for normal high-throughput production.

Source notes:

- RF FEM APT Test Manual, p.113-131

## 17. TTR / Throughput / Trace Tools / Long-Run Stability

Use for:

- reducing test time
- tuning servo and DC timing
- long-run memory issues

Main debugging levers:

- Use Power Servo Trace Viewer to reduce servo steps.
- Use DCPower Trace Viewer to find the stable current region and shrink unnecessary timing.
- Disable unnecessary result processing and tracing.
- Prefer LabVIEW RTE execution where appropriate.
- In multisite runs, specify only the DUT pins actually used.
- Shorten waveforms and unnecessary averaging when the test plan allows it.
- If memory resources are exhausted after many DUTs, use DETT and inspect leaked references.
- After major test-time reductions, recheck correlation so throughput gains do not silently shift measurement behavior.

Source notes:

- Reference Solution, p.12-13
- RF FEM APT Test Manual, p.132-142

## 18. DPAT

Use for:

- dynamic part average testing setup questions
- DPAT limits, update modes, and software bins

Main debugging levers:

- Confirm plugin files are installed in the right callback locations.
- Choose the right statistics type, sampling mode, sigma count, and window size.
- Make sure the intended tests are enabled for DPAT and mapped to the right software bins.
- Review the generated DPAT limit history after execution.

Source notes:

- RF FEM APT Test Manual, p.143-146

## 19. External Filter Box For PAMiD

Use for:

- PAMiD path-expansion design questions
- external switch/filter-box setup issues
- harmonic measurement resource planning

Main debugging levers:

- Use this when STS RF ports are insufficient or harmonic performance needs exceed the direct STS path.
- Verify switch-box power and control wiring.
- Confirm multiplexer, relay, and pin-map definitions are correct per site.
- Avoid placing isolation-sensitive ports in the same grouped path when the topology forbids it.
- Add a Filter Box Power Up step in Process Setup and explicitly connect the needed path before each measurement.

Source notes:

- RF FEM APT Test Manual, p.147-152
