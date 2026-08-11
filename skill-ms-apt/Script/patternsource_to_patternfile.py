#!/usr/bin/env python3
"""
Deterministic pin-update and compilation tool for NI Digital Pattern files.

Workflow:
  1. Parse DUTPin names from a PinMap XML file.
  2. For each .digipatsrc file, update the pin list in the
     `pattern <name>(<pin_list>)` declaration using a 4-priority
     matching strategy.
  3. (Optional) Compile each updated source with the NI Digital
     Pattern Compiler.

Usage:
  py -3.11 patternsource_to_patternfile.py \
    --input-dir <folder_with_digipatsrc_and_pinmap> \
    --output-dir <output_folder> \
    [--compile] [--compiler-path <path_to_exe>]

If --input-dir contains exactly one .pinmap file, it is used
automatically.  All .digipatsrc files in the folder are processed.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ────────────────────────────────────────────────────────────
# A.  PinMap XML parsing
# ────────────────────────────────────────────────────────────

NS = {"pm": "http://www.ni.com/TestStand/SemiconductorModule/PinMap.xsd"}

DEFAULT_COMPILER = (
    r"C:\Program Files\National Instruments"
    r"\Digital Pattern Compiler\DigitalPatternCompiler.exe"
)


def parse_pinmap_pins(pinmap_path: str | Path) -> list[str]:
    """Return a list of DUTPin names from a PinMap XML file."""
    tree = ET.parse(str(pinmap_path))
    root = tree.getroot()
    pins: list[str] = []
    for dut_pin in root.findall(".//pm:DUTPin", NS):
        name = dut_pin.get("name")
        if name:
            pins.append(name)
    if not pins:
        raise ValueError(f"No <DUTPin> elements found in {pinmap_path}")
    return pins


# ────────────────────────────────────────────────────────────
# B.  4-priority pin matching
# ────────────────────────────────────────────────────────────

def find_best_pin_match(pattern_pin: str, pinmap_pins: list[str]) -> str:
    """
    4-priority matching strategy:
      1. Exact match (case-insensitive)
      2. Component match (split PinMap pin by '_', check membership)
      3. Prefix match (PinMap pin starts with pattern pin)
      4. Substring match (pattern pin anywhere inside PinMap pin)
      5. No match → keep original
    """
    lower = pattern_pin.lower()

    # Priority 1 – exact
    for pm in pinmap_pins:
        if pm.lower() == lower:
            return pm

    # Priority 2 – component
    for pm in pinmap_pins:
        if lower in pm.lower().split("_"):
            return pm

    # Priority 3 – prefix
    for pm in pinmap_pins:
        if pm.lower().startswith(lower):
            return pm

    # Priority 4 – substring
    for pm in pinmap_pins:
        if lower in pm.lower():
            return pm

    return pattern_pin  # no match


# ────────────────────────────────────────────────────────────
# C.  Pattern declaration update
# ────────────────────────────────────────────────────────────

_PATTERN_DECL_RE = re.compile(r"(pattern\s+\w+\s*\()([^)]+)(\))")


def update_pattern_source(
    source_path: str | Path,
    output_path: str | Path,
    pinmap_pins: list[str],
) -> dict:
    """
    Read a .digipatsrc, update the pattern declaration pin list,
    write the result to output_path.

    Returns a dict:
      {
        "source": source_path,
        "output": output_path,
        "original_pins": [...],
        "updated_pins": [...],
        "changed": bool,
      }
    """
    with open(source_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    original_pins: list[str] = []
    updated_pins: list[str] = []
    changed = False
    updated_lines: list[str] = []

    for line in lines:
        m = _PATTERN_DECL_RE.search(line)
        if m:
            prefix = m.group(1)
            pin_list_str = m.group(2)
            suffix = m.group(3)
            orig = [p.strip() for p in pin_list_str.split(",")]
            matched = [find_best_pin_match(p, pinmap_pins) for p in orig]
            original_pins = orig
            updated_pins = matched
            if orig != matched:
                changed = True
            # Rebuild the line, preserving leading whitespace
            leading = line[: line.index(m.group(0))]
            trailing = line[line.index(m.group(0)) + len(m.group(0)) :]
            new_decl = f"{prefix}{', '.join(matched)}{suffix}"
            updated_lines.append(f"{leading}{new_decl}{trailing}")
        else:
            updated_lines.append(line)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.writelines(updated_lines)

    return {
        "source": str(source_path),
        "output": str(output_path),
        "original_pins": original_pins,
        "updated_pins": updated_pins,
        "changed": changed,
    }


# ────────────────────────────────────────────────────────────
# D.  Compilation
# ────────────────────────────────────────────────────────────

def resolve_compiler(user_path: str | None) -> str | None:
    """Try user path, default path, then PATH search."""
    candidates = []
    if user_path:
        candidates.append(user_path)
    candidates.append(DEFAULT_COMPILER)

    for c in candidates:
        if os.path.isfile(c):
            return c

    # Try system PATH
    found = shutil.which("DigitalPatternCompiler")
    if found:
        return found

    return None


def compile_pattern(
    compiler: str,
    source_path: str | Path,
    output_dir: str | Path,
    pinmap_path: str | Path,
) -> tuple[bool, str]:
    """
    Run the NI Digital Pattern Compiler.
    Returns (success, message).
    """
    cmd = [
        compiler,
        str(source_path),
        "-outdir",
        str(output_dir),
        "-pinmap",
        str(pinmap_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            stem = Path(source_path).stem
            digipat = Path(output_dir) / f"{stem}.digipat"
            if digipat.exists():
                return True, str(digipat)
            else:
                return False, f"Compiler returned 0 but {digipat} not found"
        else:
            msg = (result.stderr or result.stdout or "unknown error").strip()
            return False, f"Compiler exit code {result.returncode}: {msg}"
    except FileNotFoundError:
        return False, f"Compiler not found at: {compiler}"
    except subprocess.TimeoutExpired:
        return False, "Compiler timed out after 120s"


# ────────────────────────────────────────────────────────────
# E.  Main
# ────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update pattern source pin declarations and optionally compile."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Folder containing .digipatsrc and .pinmap files",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output folder for updated sources and compiled patterns",
    )
    parser.add_argument(
        "--pinmap",
        default=None,
        help="Explicit .pinmap path (auto-detected if omitted)",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        default=False,
        help="Compile updated sources with NI Digital Pattern Compiler",
    )
    parser.add_argument(
        "--compiler-path",
        default=None,
        help="Override path to DigitalPatternCompiler.exe",
    )
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    updated_dir = output_dir / "updated_sources"

    # ── Validate input folder ──
    if not input_dir.is_dir():
        print(f"ERROR: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    digipatsrc_files = sorted(input_dir.glob("*.digipatsrc"))
    if not digipatsrc_files:
        print(f"ERROR: No .digipatsrc files found in {input_dir}", file=sys.stderr)
        return 1

    # ── Resolve PinMap ──
    if args.pinmap:
        pinmap_path = Path(args.pinmap).resolve()
    else:
        pinmaps = list(input_dir.glob("*.pinmap"))
        if len(pinmaps) == 0:
            print(f"ERROR: No .pinmap file found in {input_dir}", file=sys.stderr)
            return 1
        if len(pinmaps) > 1:
            names = ", ".join(p.name for p in pinmaps)
            print(
                f"ERROR: Multiple .pinmap files found ({names}). "
                "Use --pinmap to specify one.",
                file=sys.stderr,
            )
            return 1
        pinmap_path = pinmaps[0]

    if not pinmap_path.is_file():
        print(f"ERROR: PinMap file not found: {pinmap_path}", file=sys.stderr)
        return 1

    # ── Resolve compiler (if requested) ──
    compiler_exe = None
    if args.compile:
        compiler_exe = resolve_compiler(args.compiler_path)
        if not compiler_exe:
            print(
                "ERROR: NI Digital Pattern Compiler not found. "
                f"Checked: {args.compiler_path or DEFAULT_COMPILER} and PATH.",
                file=sys.stderr,
            )
            return 1
        print(f"Compiler: {compiler_exe}")

    # ── Parse PinMap ──
    try:
        pinmap_pins = parse_pinmap_pins(pinmap_path)
    except Exception as exc:
        print(f"ERROR: Failed to parse PinMap: {exc}", file=sys.stderr)
        return 1

    print(f"PinMap: {pinmap_path}  ({len(pinmap_pins)} DUT pins)")
    print(f"Input:  {input_dir}  ({len(digipatsrc_files)} .digipatsrc files)")
    print(f"Output: {output_dir}")
    print()

    # ── Process each source file ──
    results = []
    for src in digipatsrc_files:
        dst = updated_dir / src.name
        info = update_pattern_source(src, dst, pinmap_pins)
        results.append(info)
        status = "UPDATED" if info["changed"] else "unchanged"
        print(f"  {src.name}: {status}")
        if info["changed"]:
            for o, n in zip(info["original_pins"], info["updated_pins"]):
                if o != n:
                    print(f"    {o} -> {n}")

    updated_count = sum(1 for r in results if r["changed"])
    print(
        f"\nPin update complete: {updated_count}/{len(results)} file(s) modified."
    )

    # ── Compile ──
    if args.compile and compiler_exe:
        print(f"\nCompiling with: {compiler_exe}")
        os.makedirs(output_dir, exist_ok=True)
        compile_ok = 0
        compile_fail = 0
        for info in results:
            updated_src = info["output"]
            ok, msg = compile_pattern(compiler_exe, updated_src, output_dir, pinmap_path)
            if ok:
                compile_ok += 1
                print(f"  COMPILED: {Path(updated_src).name} -> {msg}")
            else:
                compile_fail += 1
                print(f"  FAILED:   {Path(updated_src).name}: {msg}")

        print(
            f"\nCompilation complete: {compile_ok} succeeded, {compile_fail} failed."
        )
        if compile_fail > 0:
            return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
