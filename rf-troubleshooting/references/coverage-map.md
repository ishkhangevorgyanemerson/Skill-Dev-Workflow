# Coverage Map

This map shows how the current skill covers the full troubleshooting scope of the two PDFs rather than only a subset of common RF symptoms.

## Reference Solution For Semi RFIC Production Test

| PDF Topic | Covered In |
| --- | --- |
| Environment setup, pin map, waveform prep | `topic-playbook.md` sections 1 and 15 |
| Offline coding | `troubleshooting-summary.md`, `isolation-workflow.md` |
| DUT bring-up | `troubleshooting-summary.md`, `isolation-workflow.md`, `topic-playbook.md` section 1 |
| Debugging Bin1 | `troubleshooting-summary.md`, `isolation-workflow.md` |
| Data correlation | `troubleshooting-summary.md`, `symptom-taxonomy.md`, `isolation-workflow.md` |
| Multi-site execution | `troubleshooting-summary.md`, `symptom-taxonomy.md`, `isolation-workflow.md` |
| Test-time optimization | `topic-playbook.md` section 17 |
| Troubleshooting guide: Gain / PAE / P1dB / IP3 / Harmonic / ACP / EVM / SEM / NF / S-parameter / Switch Time | `symptom-taxonomy.md` plus `topic-playbook.md` sections 2-14 |

## RF FEM APT Test Manual

| PDF Chapter | Covered In |
| --- | --- |
| 1. NI Solution System Overview | `topic-playbook.md` section 1 |
| 2. Gain | `symptom-taxonomy.md`, `topic-playbook.md` section 2 |
| 3. PAE | `symptom-taxonomy.md`, `topic-playbook.md` section 3 |
| 4. IL/ISO | `topic-playbook.md` section 4 |
| 5. P1dB | `topic-playbook.md` section 5 |
| 6. IP3 | `topic-playbook.md` section 6 |
| 7. Harmonic | `topic-playbook.md` section 7 |
| 8. ACP | `symptom-taxonomy.md`, `topic-playbook.md` section 8 |
| 9. EVM & DEVM | `symptom-taxonomy.md`, `topic-playbook.md` sections 9-10 |
| 10. SEM | `symptom-taxonomy.md`, `topic-playbook.md` section 11 |
| 11. Noise Figure | `symptom-taxonomy.md`, `topic-playbook.md` section 12 |
| 12. S Parameters | `symptom-taxonomy.md`, `topic-playbook.md` section 13 |
| 13. Switch Time | `symptom-taxonomy.md`, `topic-playbook.md` section 14 |
| 14. Waveform Creator | `topic-playbook.md` section 15 |
| 15. WIFI DPD | `topic-playbook.md` section 16 |
| 16. TTR | `symptom-taxonomy.md`, `topic-playbook.md` section 17 |
| 17. DPAT | `topic-playbook.md` section 18 |
| 18. External filter Box for PAMID | `topic-playbook.md` section 19 |

## Intended Use

When the user asks a troubleshooting question:

1. Classify the problem by **symptom** using `symptom-taxonomy.md`.
2. Classify the problem by **topic domain** using `topic-playbook.md`.
3. Use `isolation-workflow.md` to choose the debugging order.
4. Use `troubleshooting-summary.md` to ground the answer in the cross-cutting patterns from the source PDFs.

If a future topic is added to the PDFs and is not listed here, this file should be updated so the skill remains visibly complete.
