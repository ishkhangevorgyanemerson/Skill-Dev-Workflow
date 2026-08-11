import re
from typing import Optional


def norm(s):
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip())


def normalize_token(s):
    s = norm(s)
    s = s.replace(".0", "")
    s = s.replace(".5", "P5")
    s = s.replace(".", "P")
    s = s.replace("MHz", "M").replace("Mhz", "M").replace("mhz", "M")
    s = s.replace("/", "_").replace("-", "_").replace(" ", "_")
    s = s.replace("(", "").replace(")", "")
    s = re.sub(r"__+", "_", s)
    return s.strip("_")


def canonical_header(s):
    x = norm(s).lower()
    return re.sub(r"[^a-z0-9]+", "", x)


def semantic_header_hints():
    return {
        "description": {
            "testdescription",
            "testitemdescription",
            "itemdescription",
            "description",
            "testitemdesc",
            "itemdesc",
            "specitem",
            "testitem",
        },
        "condition": {"testcondition", "condition", "tc", "testcond"},
        "mode": {"mode", "testmode", "rftestmode"},
        "waveform": {"waveform", "modulation", "signalwaveform"},
        "freq": {"freq", "frequency", "freqmhz"},
        "pin": {"pin", "pinpower", "pinindbm"},
        "pout": {"pout", "poutpower", "poutindbm"},
        "test_no": {"testno", "testnumber", "testid", "id"},
    }


def find_semantic_columns(ws):
    hints = semantic_header_hints()
    best = {"header_row": None, "columns": {}, "score": -1}

    for r in range(1, min(ws.max_row, 8) + 1):
        cols = {}
        score = 0
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if not isinstance(v, str) or not v.strip():
                continue
            key = canonical_header(v)
            for concept, vocab in hints.items():
                if key in vocab:
                    cols.setdefault(concept, c)
                    score += 2
                elif (
                    concept in {"description", "condition", "waveform"}
                    and concept in key
                ):
                    cols.setdefault(concept, c)
                    score += 1
        if "description" in cols:
            score += 3
        if "freq" in cols and ("pin" in cols or "pout" in cols):
            score += 3
        if score > best["score"]:
            best = {"header_row": r, "columns": cols, "score": score}

    hr = best["header_row"]
    cols = best["columns"]
    if hr is None or "description" not in cols:
        return None

    desc_col = cols["description"]
    content_score = 0
    seen = 0
    for r in range(hr + 1, min(ws.max_row, hr + 120) + 1):
        v = ws.cell(r, desc_col).value
        s = norm(v)
        if not s:
            continue
        seen += 1
        sl = s.lower()
        if re.search(r"\b(tx|rx|aclr|evm|pout|pin|gain|dbm|mhz|mpr|lpm|hpm)\b", sl):
            content_score += 2
        elif "_" in s:
            content_score += 1

    if seen == 0:
        return None
    if content_score < max(8, int(seen * 0.25)):
        return None

    return {
        "header_row": hr,
        "columns": cols,
        "score": best["score"],
        "content_score": content_score,
        "sample_size": seen,
    }


def parse_semantic_rf_description(desc: str):
    s = norm(desc)
    tokens = [t for t in re.split(r"[_\s]+", s) if t]
    up = [t.upper() for t in tokens]
    joined = "_".join(up)

    domain = ""
    for t in up:
        if t in {"TX", "RX", "DC", "IDLE"}:
            domain = t
            break

    tech = ""
    for t in up:
        if t in {"NR", "LTE", "WCDMA", "GSM"}:
            tech = t
            break

    freq = ""
    for t in up:
        if re.match(r"^\d+(P\d+)?M(HZ)?$", t):
            freq = t.replace("MHZ", "M")
            break

    power = ""
    for t in up:
        if re.match(r"^\d+(P\d+)?DBM$", t):
            power = t.lower().replace("dbm", "dBm")
            break

    profile = ""
    for t in up:
        if t.startswith("MPR") or t in {"LPM", "HPM", "CW", "SERVO"}:
            profile = t
            break

    metric = ""
    metric_rules = [
        ("E_UTRA_ACLR1L", "ACLR1L"),
        ("E_UTRA_ACLR1U", "ACLR1U"),
        ("UTRA1_ACLR", "ACLR_UTRA1"),
        ("UTRA2_ACLR", "ACLR_UTRA2"),
        ("ACLR", "ACLR"),
        ("EVM", "EVM"),
        ("POUT", "Pout"),
        ("PIN", "Pin"),
        ("GAIN", "Gain"),
        ("ICQ", "Icq"),
        ("IDLE", "Idle"),
        ("RETURN_LOSS", "ReturnLoss"),
        ("S11", "S11"),
    ]
    for pat, val in metric_rules:
        if pat in joined:
            metric = val
            break

    return {
        "domain": domain,
        "tech": tech,
        "freq": freq,
        "power": power,
        "profile": profile,
        "metric": metric,
    }


def infer_spec_update_step(
    description,
    test_condition="",
    mode="",
    waveform="",
    freq_col="",
    pin_col="",
    pout_col="",
):
    parsed = parse_semantic_rf_description(description)

    tc = normalize_token(test_condition)
    mode_n = normalize_token(mode)
    wave_n = normalize_token(waveform)
    freq = parsed["freq"] or normalize_token(freq_col).upper().replace("MHZ", "M")

    power = parsed["power"]
    if not power:
        p = norm(pout_col) or norm(pin_col)
        if re.match(r"^\d+(\.\d+)?$", p):
            power = p.replace(".", "P") + "dBm"
        elif p:
            power = normalize_token(p)

    profile = parsed["profile"]
    tech = parsed["tech"]
    domain = parsed["domain"] or (
        "TX" if norm(description).upper().startswith("TX_") else ""
    )

    key = (
        tc,
        mode_n,
        wave_n,
        domain,
        tech,
        freq,
        profile,
        normalize_token(power),
    )

    method = normalize_token(f"{mode_n}_{wave_n}").strip("_")
    parts = [domain, tech, tc, freq, profile, power, method]
    parts = [p for p in parts if p]
    step = "_".join(parts)
    if not step:
        step = normalize_token(description)

    return {
        "group_key": key,
        "step_name": step,
        "metric": parsed["metric"],
    }


def detect_style_from_sheet(
    ws, workbook_sheet_names=None, selected_sheet_name=None
) -> str:
    def g(r, c):
        return ws.cell(r, c).value

    title = str(ws.title)
    row1 = "".join(str(g(1, c) or "") for c in range(1, 12))
    row2 = "".join(str(g(2, c) or "") for c in range(1, 30))
    row3 = "".join(str(g(3, c) or "") for c in range(1, 30))
    row4 = "".join(str(g(4, c) or "") for c in range(1, 30))
    row7 = "".join(str(g(7, c) or "") for c in range(1, 12))
    names = [str(s) for s in (workbook_sheet_names or [])]
    row2_lower = row2.lower()
    row3_lower = row3.lower()
    # E6 evaluation form
    if (
        "test name" in row2_lower
        and ("ni evalution" in row2_lower or "ni evaluation" in row2_lower)
        and "testtime_1site" in row3_lower
        and "testtime_4site" in row3_lower
    ):
        return "E6"
    # E6 original form before NI columns are inserted
    if (
        ("Test Condition" in row1 or "Test Time Evaluation" in title)
        and (
            "Test Name" in row2
            and "DC Condition (V)" in row2
            and "RF Conditions" in row2
        )
        and ("MOSFET" in row3 and "Mipi" in row3 and "(dBm)" in row4)
    ):
        return "E6"
    # LIMIT_RF / LIMIT_Simplify
    row2_vals = [str(g(2, c) or "").strip() for c in range(1, 18)]
    if (
        "LIMIT_Simplify" in title or "LIMIT_simplify" in title or "LIMIT" in title
    ) and (
        "test id" in row2_vals
        and "Item" in row2_vals
        and "Test Description" in row2_vals
    ):
        return "LIMIT_RF"
    sem = find_semantic_columns(ws)
    if sem is not None and ("spec_update" in title.lower() or sem["score"] >= 9):
        return "SPEC_UPDATE"
    # legacy detections kept concise
    if (
        "Test Number" in row1
        and "TestNameMod" in row1
        and "Spec_Name" in "".join(str(g(2, c) or "") for c in range(1, 20))
    ):
        return "E5"
    if title == "Test Condition" or any(
        str(s).strip() == "Test Condition" for s in names
    ):
        if title == "Test Condition":
            return "E2"
    if "Test Number" in row1 and "Test Name" in row1:
        return "E4"
    if "Test name" in row7 and "Test #" in row7:
        return "E3"
    if "对客户端释放的Test Item" in row2 + row3:
        return "E1"
    return "UNKNOWN"


# E5 helper


def infer_e5_from_block(first_test: str, note_label: str) -> Optional[str]:
    t = norm(first_test)
    note = norm(note_label)
    if note == "DC Test":
        return "DC Pre-check (OS + Leakage)"
    if note == "DC_check":
        return "DC Post-check and leakage delta"
    m_idle = re.match(r"(N\d+)_(\d+)_(ANT\d)_(HPM|LPM)_Idle", t)
    if m_idle:
        band, freq, ant, mode = m_idle.groups()
        return f"{band}_{freq}_{ant}_{mode}_Idle"
    m_tx = re.match(r"Pin_(N\d+)_(\d+)_(ANT\d)_(HPM|LPM)_(MPR0|MPR3|MPR6P5|CW)", t)
    if m_tx:
        band, freq, ant, mode, profile = m_tx.groups()
        return f"{band}_{freq}_{ant}_{mode}_{profile}"
    return None


# E6 helpers


def infer_e6_family(
    name: str, setting: str = "", pout=None, freq: str = "", waveform: str = ""
) -> Optional[str]:
    n = norm(name)
    if n.startswith("OS1_"):
        return "OS1:\n 4 SMU Pins+2 Digital Pins"
    if n.startswith("OS2_"):
        return "OS2:\n 4 SMU Pins+2 Digital Pins"
    if n.startswith(("Leakage1_", "leakage_")):
        return "Leakage1:\n(9 SMUPins + VIO+CLK/Data)\n"
    if n.startswith("leakage2_"):
        return "Leakage2:\n(3 SMUPins + VIO+CLK/Data)"
    if n.endswith("_Capacitor"):
        return "VCC Capcitor"
    if n == "Mipi_Function":
        return "mipi function"
    if n.startswith("IL_"):
        return "SpecAn Txp"
    if n.startswith(("2f_", "3f_")):
        return "SpecAn Servo+Har2"
    if n.startswith("Isolation_"):
        return "SpecAn Servo+ 2 Iso"
    if n.startswith("ASEM_"):
        return "ASEM, Servo with ACP"
    if "_LPM_" in n:
        if "HB1_LPM" in n:
            return "5G TDD 100M, Servo\n(无EVM/ACP, PTE按10M评估）"
        if "MB4_LPM" in n:
            return "5G FDD 50M, Servo\n(无EVM/ACP, PTE按10M评估）"
        if "LB1(L1)_LPM" in n:
            return "5G FDD 20M, Servo\n(无EVM/ACP, PTE按10M评估）"
    if "HB3_4G" in n:
        return "4G_TDD, Servo with Idle"
    if "HB2_4G" in n:
        return "4G_TDD, Servo"
    if "HB1_5G_N41" in setting or "HB1_NT_M100R273P3" in n:
        return "5G TDD 100M, Servo"
    if "HB1_5G_N40" in setting or "HB1_NT_M80R217P6.5" in n:
        return "5G TDD 80M, Servo"
    if "MB1_5G" in setting or "MB1_" in n:
        return "5G_FDD 20M, Servo with Idle"
    if "MB2_4G" in setting or "MB2_" in n:
        return "4G_FDD, Servo"
    if "MB3_4G" in setting or "MB3_" in n:
        return "4G_FDD, Servo"
    if "MB4_5G" in setting or "MB4_" in n:
        return "5G FDD 50M, Servo"
    if "MB5_4G" in setting or "MB5_" in n:
        return "4G_TDD, Servo"
    if "LB1(L1)_5G" in setting or "LB1(L1)_" in n:
        return (
            "5G_FDD 20M, Servo with Idle"
            if n.startswith("Idle_")
            else "5G FDD 20M, Servo"
        )
    if "LB2(L1)_5G" in setting or "LB2(L1)_" in n:
        return "5G FDD 30M, Servo"
    if "LB3(L1)_5G" in setting or "LB3(L1)_" in n:
        return "5G FDD 20M, Servo"
    if "LB4(L1)_5G" in setting or "LB4(L1)_" in n:
        return "5G FDD 20M, Servo"
    if "LB5(L1)_4G" in setting or "LB5(L1)_" in n:
        return "4G_TDD, Servo"
    return None


def infer_e6_times(family: str):
    mapping = {
        "OS1:\n 4 SMU Pins+2 Digital Pins": (62, 65),
        "Leakage1:\n(9 SMUPins + VIO+CLK/Data)\n": (192, 195),
        "VCC Capcitor": (30, 32),
        "mipi function": (19, 20),
        "4G_TDD, Servo with Idle": (22, 27),
        "4G_TDD, Servo": (22, 27),
        "4G_FDD, Servo": (22, 27),
        "5G TDD 100M, Servo": (20, 31),
        "5G TDD 80M, Servo": (20, 31),
        "5G_FDD 20M, Servo with Idle": (18, 22),
        "5G FDD 20M, Servo": (18, 22),
        "5G FDD 30M, Servo": (18, 22),
        "5G FDD 50M, Servo": (19, 31),
        "5G TDD 100M, Servo\n(无EVM/ACP, PTE按10M评估）": (18, 22),
        "5G FDD 50M, Servo\n(无EVM/ACP, PTE按10M评估）": (18, 22),
        "5G FDD 20M, Servo\n(无EVM/ACP, PTE按10M评估）": (18, 22),
        "SpecAn Txp": (4, 4.5),
        "SpecAn Servo+Har2": (15, 23),
        "SpecAn Servo+ 2 Iso": (20, 28),
        "ASEM, Servo with ACP": (16, 18),
        "OS2:\n 4 SMU Pins+2 Digital Pins": (62, 65),
        "Leakage2:\n(3 SMUPins + VIO+CLK/Data)": (84, 86),
    }
    return mapping.get(family, (None, None))


# LIMIT_RF helpers
MEAS_PREFIXES = [
    "IDLE_Vbat_",
    "IDLE_Vcc1_",
    "IDLE_Vcc2_",
    "IDLE_Total_",
    "Pin_",
    "Pout_",
    "Gain_",
    "Icc_Vbat_",
    "Icc_Vcc1_",
    "Icc_Vcc2_",
    "Icc_Total_",
    "PAE_Total_",
    "E-UTRA_L_",
    "UTRA1_L_",
    "UTRA2_L_",
    "EVM_",
    "ACLR1_L_",
    "ACLR1_U_",
    "ACLR2_L_",
    "ACLR2_U_",
    "DFT_IDLE_Vbat_",
    "DFT_IDLE_Vcc1_",
    "DFT_IDLE_Vcc2_",
    "DFT_IDLE_Total_",
    "DFT_Pin_",
    "DFT_Pout_",
    "DFT_Gain_",
    "DFT_Icc_Vbat_",
    "DFT_Icc_Vcc1_",
    "DFT_Icc_Vcc2_",
    "DFT_Icc_Total_",
    "DFT_PAE_Total_",
    "DFT_ACLR1_L_",
    "DFT_ACLR1_U_",
    "DFT_EVM_",
    "CP_Pin_",
    "CP_Pout_",
    "CP_Gain_",
    "CP_Icc_Vbat_",
    "CP_Icc_Vcc1_",
    "CP_Icc_Vcc2_",
    "CP_Icc_Total_",
    "CP_PAE_Total_",
    "CP_ACLR1_L_",
    "CP_ACLR1_U_",
    "CP_EVM_",
]


def strip_prefixes(desc: str) -> str:
    x = norm(desc)
    for p in sorted(MEAS_PREFIXES, key=len, reverse=True):
        if x.startswith(p):
            return x[len(p) :]
    return x


def infer_limit_rf_mapping(
    item, desc, band, tx_port, freq, waveform, power, section, prev_mapping=None
):
    item_n = norm(item)
    desc_n = norm(desc)
    section_n = norm(section)

    if not item_n and not desc_n:
        return None

    # DC / RX families
    if item_n.startswith("OS_") or desc_n.startswith("OS_"):
        return (
            "DC_Pre_OS"
            if ("_Pre" in item_n or "_Pre" in desc_n)
            else "DC_Post_OS"
            if ("_Post" in item_n or "_Post" in desc_n)
            else "DC_OS"
        )
    if (
        item_n.startswith("Ileakage_")
        or desc_n.startswith("Ileakage_")
        or item_n.startswith("Standby_")
        or desc_n.startswith("Standby_")
        or item_n in {"MIPI_Function_Test"}
        or desc_n in {"MIPI_Function_Test"}
    ):
        return "DC_Pre_Leakage_Standby_MIPI"
    if "Check" in item_n or "Check" in desc_n or "Delta" in item_n or "Delta" in desc_n:
        return "DC_Post_Standby_Check_Delta"
    if item_n.startswith("IL_RX") or desc_n.startswith("IL_RX"):
        return "RX_Insertion_Loss"

    # Try explicit Test Description when it is not an unevaluated formula
    source = desc_n or item_n
    if source.startswith("="):
        source = ""
    core = strip_prefixes(source)
    if core and core != source:
        core = normalize_token(core)
        family = ""
        sec = section_n.lower()
        if "wcdma" in sec:
            family = "WCDMA"
        elif "5g" in sec or core.startswith("N") or "_N" in core:
            family = "NR"
        elif "lte" in sec or re.search(r"_B\d+", core):
            family = "LTE"
        elif "rx" in sec:
            family = "RX"
        return f"{family}_{core}" if family else core

    # synthesize from columns when description is formula or blank
    bits = []
    sec = section_n.lower()
    if "wcdma" in sec:
        bits.append("WCDMA")
    elif "5g" in sec or norm(band).startswith("N"):
        bits.append("NR")
    elif "lte" in sec or norm(band).startswith("B"):
        bits.append("LTE")
    for v in [tx_port, band, freq, waveform, power]:
        tok = normalize_token(v)
        if tok and tok not in {"SERVO"}:
            bits.append(tok)
    if bits:
        return "_".join(bits)
    return prev_mapping
