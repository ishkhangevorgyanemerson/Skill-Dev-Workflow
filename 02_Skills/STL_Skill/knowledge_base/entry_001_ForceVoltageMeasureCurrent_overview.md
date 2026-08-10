# Entry 001 — ForceVoltageMeasureCurrent: Overview and Common Issues

**Skill:** STL_Skill  
**Category:** TestStand Steps  
**Source:** https://github.com/ni/semi-test-library-dotnet/blob/main/SemiconductorTestLibrary.TestStandSteps/source/ForceVoltageMeasureCurrent.cs  
**Added:** 2026-08-10  
**Contributed by:** Skill Owner (example entry)

---

## Question
What does the `ForceVoltageMeasureCurrent` TestStand step do, and what are common configuration mistakes?

## Context
The step is used in semiconductor parametric testing to force a voltage on a set of pins and measure the resulting current. It is commonly used in leakage and continuity tests.

## Answer
The `ForceVoltageMeasureCurrent` step in the STL:
1. Forces a specified voltage level on the selected DUT pins via an SMU or PPMU
2. Measures the current at each pin
3. Publishes results to TestStand as a numeric limit test

**Common configuration mistakes:**
- **Missing pin map entry**: Ensure all pins used in the step are defined in the `.pinmap` file
- **Incorrect voltage level units**: Voltage is specified in Volts; do not pass millivolts
- **TSM context not initialized**: The `SemiconductorModuleContext` must be properly passed from the TestStand sequence
- **Current limit too low**: If the DUT draws more current than the configured limit, the SMU will current-limit and the measurement will be unreliable

## Code Reference
```csharp
// ForceVoltageMeasureCurrent.cs (simplified)
public static void ForceVoltageMeasureCurrent(
    ISemiconductorModuleContext tsmContext,
    string[] siteNumbers,
    string pinNames,
    double voltageLevel,
    double currentLimit)
{
    // Forces voltage and measures current on specified pins
}
```

## Resolution / Workaround
Always validate your pin map and TSM context initialization in the `Setup` callback before calling this step.

## Tags
`ForceVoltageMeasureCurrent`, `SMU`, `leakage`, `continuity`, `TSM`, `pinmap`
