# Team Knowledge Case Submission Template

Use this template for every solved case you want skills to learn from.

## 1) Case Metadata
- Case title:SMU Multiple Advance sequence 
- Date:8/11/2026
- Author:Ishkhan
- Team:
- Candidate skills`semiconductor-test-library-assistant`,
- Domains/tags (for example `stl`, `dcpower`, `csharp`:

## 2) Problem Statement
Can you give me a .Net code example that run multiple advacnde sequences. So with SMU I prpare and do all configurations for multiple advance sequences and then call the one I want?

## 3) Context and Constraints
- Project or product context:DSJ
- Hardware/instruments involved:PXIe-4190
- Software stack/API versions:
- Constraints (time, quality, licensing, safety, production limits):

## 4) References Used
- Internal docs: 
- Code paths/repositories: Semi-test-library-dotnet-main
- Vendor docs:
- Prior similar cases:

## 5) Solution Summary
- Short final answer:
- Why this approach was chosen:

## 6) Step-by-Step Resolution
1.
2.
3.

## 7) Code and Artifacts (if applicable)
- Code snippets:
```text
using NationalInstruments;
using NationalInstruments.SemiconductorTestLibrary.Common;
using static NationalInstruments.SemiconductorTestLibrary.Common.Utilities;
using NationalInstruments.SemiconductorTestLibrary.DataAbstraction;
using NationalInstruments.SemiconductorTestLibrary.InstrumentAbstraction;
using NationalInstruments.SemiconductorTestLibrary.InstrumentAbstraction.DCPower;
using NationalInstruments.SemiconductorTestLibrary.InstrumentAbstraction.Digital;
using NationalInstruments.TestStand.SemiconductorModule.CodeModuleAPI;
using NationalInstruments.ModularInstruments.NIDCPower;
using NationalInstruments.Restricted;
using System;
using System.Linq;
using System.Data.SqlTypes;
using NationalInstruments.ModularInstruments.NIDigital;
using System.Collections.Generic;
using System.Security.Cryptography;

namespace DSG_Case
{
    public static partial class TestSteps
    {
        public static NILCRMeasurement[] LcrBiasSweep(
            ISemiconductorModuleContext tsmContext,
            string[] smuPinNames,
            double lcrFrequency,
            out int sitenumber,
            double impedancerange,
            double acVoltage,
            double startDcBias = 0,
            double endDcBias = 1,
            double numberOfSteps = 1,
            double[] biasValues = null,
            bool chooseStartStopStepMode = false,
            bool opencompensation = false,
            bool shortcompensation = false,
            double lcrcustommeasurementtime = 0.001,
            double offset = 0.001,

            // Advanced sequence names
            string firstAdvancedSequenceName = "MySequence1",
            string secondAdvancedSequenceName = "MySequence2",
            string advancedSequenceNameToRun = "MySequence1",

            // Second sequence bias settings
            double[] secondBiasValues = null,
            double secondStartDcBias = 0,
            double secondEndDcBias = 1,
            double secondNumberOfSteps = 1,
            bool secondChooseStartStopStepMode = true,

            DCPowerLCRMeasurementTime LcrMeasurementTime = DCPowerLCRMeasurementTime.Medium)
        {
            int[] siteNumbers = (int[])tsmContext.SiteNumbers;

            // Input validation
            if (string.IsNullOrWhiteSpace(firstAdvancedSequenceName)) { throw new ArgumentException("First advanced sequence name cannot be null or empty.", nameof(firstAdvancedSequenceName)); }
            if (string.IsNullOrWhiteSpace(secondAdvancedSequenceName)) { throw new ArgumentException("Second advanced sequence name cannot be null or empty.", nameof(secondAdvancedSequenceName)); }
            if (firstAdvancedSequenceName == secondAdvancedSequenceName) { throw new ArgumentException("First and second advanced sequence names must be different."); }
            if (string.IsNullOrWhiteSpace(advancedSequenceNameToRun)) { throw new ArgumentException("Advanced sequence name to run cannot be null or empty.", nameof(advancedSequenceNameToRun)); }
            if (advancedSequenceNameToRun != firstAdvancedSequenceName && advancedSequenceNameToRun != secondAdvancedSequenceName) { throw new ArgumentException($"advancedSequenceNameToRun must be either '{firstAdvancedSequenceName}' or '{secondAdvancedSequenceName}'.", nameof(advancedSequenceNameToRun)); }
            if (numberOfSteps <= 0) { throw new ArgumentException("numberOfSteps must be greater than zero.", nameof(numberOfSteps)); }
            if (secondNumberOfSteps <= 0) { throw new ArgumentException("secondNumberOfSteps must be greater than zero.", nameof(secondNumberOfSteps)); }
            if (!chooseStartStopStepMode && (biasValues == null || biasValues.Length == 0)) { throw new ArgumentException("biasValues must be provided when chooseStartStopStepMode is false.", nameof(biasValues)); }
            if (!secondChooseStartStopStepMode && (secondBiasValues == null || secondBiasValues.Length == 0)) { throw new ArgumentException("secondBiasValues must be provided when secondChooseStartStopStepMode is false.", nameof(secondBiasValues)); }

            var sessionManager = new TSMSessionManager(tsmContext);
            DCPowerSessionsBundle smuSessions = sessionManager.DCPower(smuPinNames);

            int pointsToFetch = 0;
            var pointsToFetchBySequence = new Dictionary<string, int>();

            smuSessions.Do((DCPowerSessionInformation sessionInfo) =>
            {
                // Common LCR settings for both sequences
                sessionInfo.AllChannelsOutput.Source.Mode = DCPowerSourceMode.Sequence;
                sessionInfo.AllChannelsOutput.InstrumentMode = DCPowerInstrumentMode.LCR;
                sessionInfo.AllChannelsOutput.LCR.StimulusFunction = DCPowerLCRStimulusFunction.ACVoltage;
                sessionInfo.AllChannelsOutput.LCR.Frequency = lcrFrequency;
                sessionInfo.AllChannelsOutput.DeviceSpecific.LCR.CableLength = DCPowerCableLength.NIStandardTriaxial2M;
                sessionInfo.AllChannelsOutput.LCR.ImpedanceRange = impedancerange;
                sessionInfo.AllChannelsOutput.Source.Output.Enabled = true;
                sessionInfo.AllChannelsOutput.LCR.VoltageAmplitude = acVoltage;
                sessionInfo.AllChannelsOutput.LCR.Compensation.ShortCompensationEnabled = shortcompensation;
                sessionInfo.AllChannelsOutput.LCR.Compensation.OpenCompensationEnabled = opencompensation;
                sessionInfo.AllChannelsOutput.LCR.Compensation.ShortCustomCableCompensationEnabled = false;
                sessionInfo.AllChannelsOutput.LCR.DCBiasSource = DCPowerLCRDCBiasSource.Voltage;
                sessionInfo.AllChannelsOutput.LCR.MeasurementTime = LcrMeasurementTime;
                sessionInfo.AllChannelsOutput.LCR.CustomMeasurementTime = lcrcustommeasurementtime;
                sessionInfo.AllChannelsOutput.LCR.SourceDelayMode = DCPowerLCRSourceDelayMode.Automatic;

                // Helper to create one DC-bias sequence
                int ConfigureLcrDcBiasAdvancedSequence(
                    string sequenceName,
                    bool useStartStopStepMode,
                    double[] explicitBiasValues,
                    double sequenceStartDcBias,
                    double sequenceEndDcBias,
                    double sequenceNumberOfSteps)
                {
                    int sequencePointCount = Convert.ToInt32(sequenceNumberOfSteps);

                    if (sequencePointCount <= 0) { throw new ArgumentException("Sequence number of steps must be greater than zero.", nameof(sequenceNumberOfSteps)); }

                    double stepDcBias = (sequenceEndDcBias - sequenceStartDcBias) / sequencePointCount;
                    double biasSequenceValue;
                    int numberOfPoints;

                    DCPowerAdvancedSequenceProperty[] advancedSequenceProperties =
                    {
                        DCPowerAdvancedSequenceProperty.LcrDcBiasVoltageLevel
                    };

                    // Create sequence and make it active while adding steps
                    sessionInfo.AllChannelsOutput.Source.AdvancedSequencing.CreateAdvancedSequence(sequenceName, advancedSequenceProperties, true);

                    if (!useStartStopStepMode)
                    {
                        for (int pointIndex = 0; pointIndex < explicitBiasValues.Length; pointIndex++)
                        {
                            // Add step using explicit bias value
                            sessionInfo.AllChannelsOutput.Source.AdvancedSequencing.CreateAdvancedSequenceStep(true);

                            biasSequenceValue = explicitBiasValues[pointIndex] + (offset * siteNumbers[0]);

                            sessionInfo.AllChannelsOutput.LCR.DCBiasVoltageLevel = biasSequenceValue;
                        }

                        numberOfPoints = explicitBiasValues.Length;
                    }
                    else
                    {
                        for (int pointIndex = 0; pointIndex < sequencePointCount; pointIndex++)
                        {
                            // Add step using calculated bias value
                            sessionInfo.AllChannelsOutput.Source.AdvancedSequencing.CreateAdvancedSequenceStep(true);

                            biasSequenceValue = (stepDcBias * pointIndex) + sequenceStartDcBias + (siteNumbers[0] * offset);

                            sessionInfo.AllChannelsOutput.LCR.DCBiasVoltageLevel = biasSequenceValue;
                        }

                        numberOfPoints = sequencePointCount;
                    }

                    return numberOfPoints;
                }

                // Create first sequence
                pointsToFetchBySequence[firstAdvancedSequenceName] =
                    ConfigureLcrDcBiasAdvancedSequence(
                        firstAdvancedSequenceName,
                        chooseStartStopStepMode,
                        biasValues,
                        startDcBias,
                        endDcBias,
                        numberOfSteps);

                // Create second sequence
                pointsToFetchBySequence[secondAdvancedSequenceName] =
                    ConfigureLcrDcBiasAdvancedSequence(
                        secondAdvancedSequenceName,
                        secondChooseStartStopStepMode,
                        secondBiasValues,
                        secondStartDcBias,
                        secondEndDcBias,
                        secondNumberOfSteps);

                // Get fetch count for selected sequence
                pointsToFetch = pointsToFetchBySequence[advancedSequenceNameToRun];

                // Select active sequence by name
                sessionInfo.AllChannelsOutput.Source.AdvancedSequencing.ActiveAdvancedSequence =
                    advancedSequenceNameToRun;
            });

            PrecisionTimeSpan timeout = new PrecisionTimeSpan(300.0);

            // Run selected active sequence
            smuSessions.Initiate();

            smuSessions.Do((DCPowerSessionInformation sessionInfo) =>
            {
                sessionInfo.AllChannelsOutput.Events.SourceCompleteEvent.WaitForEvent(timeout);
            });

            var results = new NILCRMeasurement[0];

            // Fetch LCR results
            smuSessions.Do((DCPowerSessionInformation sessionInfo) =>
            {
                results = sessionInfo.Session.Measurement.FetchLCR(sessionInfo.AllChannelsString, timeout, pointsToFetch);
            });

            // Stop generation
            smuSessions.Abort();

            // Delete created sequences
            smuSessions.Do((DCPowerSessionInformation sessionInfo) =>
            {
                sessionInfo.AllChannelsOutput.Source.AdvancedSequencing.DeleteAdvancedSequence(
                    firstAdvancedSequenceName);

                sessionInfo.AllChannelsOutput.Source.AdvancedSequencing.DeleteAdvancedSequence(
                    secondAdvancedSequenceName);
            });

            // Reset session
            smuSessions.Do((DCPowerSessionInformation sessionInfo) =>
            {
                sessionInfo.Session.Utility.Reset();
            });

            var cpValues = results.Select(measurements => measurements.Cp).ToArray();
            var maxCp = cpValues.Max();
            var minCp = cpValues.Min();

            tsmContext.PublishResult(minCp, "C_BIAS_LOW_B", smuPinNames[0]);
            tsmContext.PublishResult(minCp, "C_BIAS_HIGH_B", smuPinNames[0]);

            sitenumber = siteNumbers[0];

            return results;
        }
    }
}
```
- Configs/commands:
```text
<paste relevant commands/config here>
```
- Output artifacts produced:

## 8) Validation Evidence
- How was correctness verified? I run it worked
- Test data or scenario:
- Result metrics / pass criteria:
I could see the sgenerated sequences
## 9) Reuse Guidance
- When should this be reused?when the ask is to create multiple advance sequences
- When should this NOT be reused?
- Known caveats and failure modes:

## 10) Data Safety Check
- [ ] No secrets/tokens/passwords
- [ ] No customer-sensitive identifiers
- [ ] No restricted proprietary data

