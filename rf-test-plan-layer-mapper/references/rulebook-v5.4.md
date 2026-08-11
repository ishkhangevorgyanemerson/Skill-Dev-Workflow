# Rulebook (v5.4)

## Global

- Ask for the main test plan sheet when there are multiple sheets.
- Run candidate-sheet discovery before guessing the target sheet.
- Do not require the user workbook to already contain a mapping column.
- Create the mapping column automatically when absent.

## E6 (NI Evaluation timing workbook)

- Detect a multi-row header with `Test Name`, `NI Evalution`, `TestTime_1site`, `TestTime_4Site`, `DC Condition (V)`, `RF Conditions`.
- Insert three columns after `Test Name` when drafting from original: `NI Evalution`, `TestTime_1site`, `TestTime_4Site`.
- NI Evaluation labels are tester-method families, not DUT-path-specific RF names.
- For `Servo with Idle` families, idle-current rows and the following active measurement rows belong to the same merged NI block.
- Timing columns must be populated and merged with the NI family block.

## LIMIT_RF (LIMIT_Simplify style)

- Detect the main limit sheet by `test id`, `Item`, `Test Description`, `Vbat/VCC1/VCC2/VIO`, `Band`, `Tx_Port`, `Freq`, `Waveform`, `Power (dBm)`, and limit columns.
- Insert one column after `Item`: `Predicted Test Step`.
- Map DC tests to family blocks:
  - `OS_*_Pre` -> `DC_Pre_OS`
  - `OS_*_Post` -> `DC_Post_OS`
  - `Ileakage_*`, `Standby_*`, `MIPI_Function_Test` -> `DC_Pre_Leakage_Standby_MIPI`
  - `*Check`, `*Delta` -> `DC_Post_Standby_Check_Delta`
  - `IL_RX*` -> `RX_Insertion_Loss`
- For RF rows, derive scenario families from explicit `Test Description` when available; otherwise synthesize from `Band + Tx_Port + Freq + Waveform + Power`.
- Merge contiguous identical step names into one visible block.
