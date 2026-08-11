---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', sans-serif;
    font-size: 22px;
  }
  h1 {
    color: #0078d4;
    font-size: 38px;
    border-bottom: 2px solid #0078d4;
    padding-bottom: 6px;
  }
  h2 {
    color: #005a9e;
    font-size: 28px;
  }
  h3 {
    color: #333;
    font-size: 22px;
  }
  code {
    background: #f3f3f3;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 18px;
  }
  pre {
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 6px;
    padding: 16px;
    font-size: 16px;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
  .tag {
    background: #0078d4;
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 14px;
  }
  .highlight-box {
    background: #e6f2fc;
    border-left: 4px solid #0078d4;
    padding: 10px 16px;
    border-radius: 4px;
    margin: 8px 0;
  }
  .success {
    background: #e6f7ee;
    border-left: 4px solid #107c10;
    padding: 10px 16px;
    border-radius: 4px;
    margin: 8px 0;
  }
  table {
    width: 100%;
    font-size: 18px;
    border-collapse: collapse;
  }
  th {
    background: #0078d4;
    color: white;
    padding: 8px;
  }
  td {
    padding: 6px 8px;
    border-bottom: 1px solid #ddd;
  }
  tr:nth-child(even) td {
    background: #f5f5f5;
  }
---

# RF Troubleshooting Skill
## From Raw Documents → Intelligent Copilot Assistant

**Skill Location:** `C:\Repos\Semi-Skills-Hub\skills\rf-troubleshooting`

GitHub Copilot · VS Code · NI STS / RFmx Production Test

---

# Slide 1 — Building the Skill from Raw Documents

## Concept: What Is a "Skill"?

A **Skill** is a structured knowledge package that teaches GitHub Copilot **domain-specific expertise** by attaching a `SKILL.md` instruction file and curated reference documents. It converts static PDFs and DOCs into an **interactive AI reasoning engine**.

---

<div class="columns">

<div>

### Step 1 — Gather Raw Source Material

Raw input documents (PDFs and DOCs provided by subject-matter experts):

```
📄 Reference Solution for Semi RFIC Production Test.pdf
📄 RF FEM APT Test Manual.pdf
📄 (optional) Additional DUT characterization notes.docx
```

> These PDFs cover gain, PAE, EVM, IP3, DPD, SEM, switch time, DPAT, and more — **~1,000 pages of RF test knowledge**.

</div>

<div>

### Step 2 — Extract and Distill into Reference Markdown Files

Use a skill-creator assistant (or manually) to convert each PDF chapter into structured, AI-readable references:

```
skills/rf-troubleshooting/
├── SKILL.md                   ← Master instruction file
└── references/
    ├── coverage-map.md        ← Maps PDF chapters → reference files
    ├── topic-playbook.md      ← Domain-specific debug guidance
    ├── symptom-taxonomy.md    ← Symptom → first checks
    ├── isolation-workflow.md  ← Step-by-step fault isolation
    └── troubleshooting-summary.md  ← Cross-cutting principles
```

</div>

</div>

---

### Step 3 — Write the SKILL.md Instruction File

`SKILL.md` is the **brain of the skill**. It tells Copilot:

| Section | Purpose |
|---|---|
| `## Read These References First` | Which reference files to consult for each problem type |
| `## Workflow` | Classify → Ask → Isolate → Advise |
| `## Missing-Info Gate` | Never guess critical RF parameters; ask first |
| `## Required Response Format` | Structured: Framing → Causes → Checks → Path |
| `## High-Value Heuristics` | Condensed rules from ~1,000 pages of source material |

<div class="highlight-box">

**Key design principle:** Reference files stay separate from the instruction file. Copilot reads only what it needs, keeping each response focused and grounded.

</div>

### Step 4 — Deploy the Skill

Copy the skill folder to your personal or project skill location:

```text
~/.copilot/skills/rf-troubleshooting/    ← personal (all workspaces)
.github/skills/rf-troubleshooting/       ← project-scoped
```

---

# Slide 2 — Using the Skill in VS Code with GitHub Copilot

## Real Example: WLAN EVM Troubleshooting

**Scenario:** A test engineer reports that WLAN 802.11b/g EVM measured on NI STS is **-38 dB**, but the expected value is **-35 dB** — **3 dB worse than expected**.

---

### How to Invoke the Skill in VS Code

Open GitHub Copilot Chat in VS Code, then attach the skill as context:

```
#prompt:SKILL.md  Follow instructions in #prompt:SKILL.md with these arguments:
I'm using RF steps to measure EVM for WLAN DUT, but the measured EVM
value is 3 dB smaller than expected. How to troubleshoot?
```

> **Note:** In VS Code Copilot Chat, drag-and-drop `SKILL.md` into the chat input or use the **Attach context** button and select the file. The `#prompt:SKILL.md` reference loads the full skill instruction into the model's context.

---

### What Copilot Does Next — The Missing-Info Gate

Because critical parameters (standard, environment, loopback status) were not yet provided, the skill's **Missing-Info Gate** triggers. Copilot asks **only the blocking questions**:

<div class="columns">

<div>

**Copilot prompts (structured dialogs):**

1. 📋 What are expected and measured EVM values?
   → *User: Expected = −35 dB, Measured = −38 dB*

2. 📋 Which WLAN standard?
   → *User: 802.11b/g*

3. 📋 Measurement offset / trigger configuration?
   → *User: Using measurement offset*

4. 📋 Have you verified loopback EVM?
   → *User: Loopback is also smaller*

</div>

<div class="highlight-box" style="margin-top: 20px">

**Why this matters:**

The loopback answer is the key pivot — it tells Copilot that the 3 dB gap is **not a path loss or DUT issue**, but a **measurement-configuration issue**.

Without this gate, a generic assistant would have listed 10 vague possibilities including DUT defects.

</div>

</div>

---

### Copilot's Structured Response (After Collecting Context)

<div class="columns">

<div>

**Problem Framing**
- Symptom: EVM −38 dB vs expected −35 dB (3 dB worse)
- Key finding: **Loopback also worse** → path/DUT eliminated
- Most likely layer: Measurement configuration

**Most Likely Causes**
1. Measurement offset misaligned to waveform structure
2. Measurement length too short (weak averaging)
3. Channel-estimation or frequency-error method mismatch vs bench

</div>

<div>

**Recommended Checks (ordered)**

1. Verify `SymbolOffset` aligns to valid data-symbol region in RFmx WLAN — inspect in **RFmx Soft Front Panel**
2. Increase `MeasurementLength` to ≥10 symbols; match bench config
3. Compare `ChannelEstimationMode` and `FrequencyErrorEstimationMethod` settings with bench reference
4. Confirm `ReferenceLevel` is 5 dB above average signal power
5. Cross-check: load bench waveform on ATE and rerun loopback

</div>

</div>

<div class="highlight-box">

**Quick Isolation Path:** Offset alignment → Measurement length → Channel estimation settings → Reference level → Waveform file integrity

</div>

> **Source Notes:** RF FEM APT Test Manual p.78–81 · Reference Solution p.10–14

---

# Slide 3 — How GitHub Copilot + Skill Helped

## Value Delivered: Before vs. After

<div class="columns">

<div>

### Without the Skill
**Generic Copilot answer:**
- EVM can be affected by noise, interference, modulation errors, hardware issues...
- Check your signal generator, cables, DUT biasing, test firmware, driver version...
- Consider re-running calibration...

> 🔴 **15+ vague suggestions**, no prioritization, no production-test context, engineer wastes hours checking irrelevant paths.

</div>

<div>

### With the Skill
**Skill-guided Copilot answer:**
- **Asked first** before guessing (loopback status was pivotal)
- **Loopback = also worse** → immediately eliminated path/cable/DUT as cause
- Focused on **3 actionable measurement-config checks** in priority order
- Referenced the **exact RFmx parameters** to inspect
- Pointed to the **RFmx Soft Front Panel** for visual verification

> 🟢 **Root cause isolated in one session**, engineer checks 3 parameters instead of 15 guesses.

</div>

</div>

---

## What Made the Difference

| Capability | How It Helped in This Example |
|---|---|
| **Missing-Info Gate** | Asked for loopback result first — the single most discriminating fact |
| **Symptom Taxonomy** | "Loopback also wrong" → immediately mapped to measurement-config layer |
| **Topic Playbook (EVM)** | Loaded 802.11b/g-specific checks: offset, length, channel estimation |
| **Isolation-by-Layer** | Cleared path/calibration layer first before entering measurement layer |
| **Source-backed Heuristics** | "Verify offset/length, channel estimation, loopback first" — from RF FEM APT Manual p.78–81 |
| **Structured Response Format** | Framing → Causes → Ordered Checks → Isolation Path → Source Notes |

---

## The Broader Skill Coverage

This same skill handles **all topics from two full RF test references**:

<div class="columns">

<div>

- Gain / Servo / Vramp servo
- PAE / Icc / DC timing
- IL / ISO / PAVT segmented measurements
- P1dB / AMPM ramp compression
- IP3 / IM3 two-tone setup
- Harmonic (sub-6 GHz, >6 GHz, >8.5 GHz)

</div>

<div>

- ACP / ACLR offset definitions
- **EVM / DEVM / WLAN DPD**
- SEM stability and offset logic
- Noise Figure
- S-parameters / user calibration
- Switch Time / trigger sequencing
- TTR throughput and memory leaks

</div>

</div>

<div class="success">

**Net result:** One skill turns ~1,000 pages of NI RF test expertise into an **interactive, interactive, production-aware troubleshooting partner** — available instantly inside VS Code, without leaving the engineering workflow.

</div>

---

## Summary

```
Raw PDFs + DOCs
      ↓  (skill-creator + SME distillation)
SKILL.md + 5 structured reference files
      ↓  (deploy to ~/.copilot/skills/)
GitHub Copilot in VS Code gains RF test domain expertise
      ↓  (#prompt:SKILL.md + user question)
Structured fault isolation: ask → classify → layer → advise
      ↓
Engineer finds root cause faster, with fewer wrong turns
```

> **Skill location:** `C:\Repos\Semi-Skills-Hub\skills\rf-troubleshooting`
> **Invoke via:** Attach `SKILL.md` in Copilot Chat as `#prompt:SKILL.md`
