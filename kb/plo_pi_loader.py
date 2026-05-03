"""
kb/plo_pi_loader.py
===================
Parse ``KB_PLO_PI_Matrix_1.md`` at import time — this file IS the single
source of truth for all PLO / PI / IRMA data.

The file is located at the repository root (OBE_AGent_DCCT/).

Supported programs: "CNTT" | "HTTT" | "KHMT"

Public API
----------
get_pi_list(program)                    -> List[str]
get_plo_description(plo_code, program)  -> str
get_pi_description(pi_code, program)    -> str
get_course_irma(course_code, program)   -> Dict[str, str]
get_plo_for_pi(pi_code, program)        -> str

Internal structure loaded from the MD file
------------------------------------------
_DATA["CNTT"] = {
    "plo":        { "PLO1": "...", "PLO4": "...", ... },
    "pi":         { "PLO1": { "PI1.1": "...", ... }, ... },
    "course_map": { "FIT3001": { "PI2.1": "I" }, ... },
}
"""

import re
from pathlib import Path
from typing import Dict, List


# ─── Locate KB file ───────────────────────────────────────────────────────────

def _find_kb_file() -> Path:
    """Search for KB_PLO_PI_Matrix_1.md starting from the repo root."""
    here    = Path(__file__).resolve().parent   # AI_Agent_OBE_IN_DNU/kb/
    project = here.parent                        # AI_Agent_OBE_IN_DNU/
    root    = project.parent                     # OBE_AGent_DCCT/

    for base in (root, project, Path.cwd(), Path.cwd().parent):
        for name in ("KB_PLO_PI_Matrix_1.md", "KB_PLO_PI_Matrix.md"):
            p = base / name
            if p.is_file():
                return p

    raise FileNotFoundError(
        "KB_PLO_PI_Matrix_1.md not found. "
        "Place the file at the repository root (OBE_AGent_DCCT/)."
    )


# ─── Compiled regex helpers ───────────────────────────────────────────────────

_RE_SECTION   = re.compile(r"^##\s+PHẦN\s+(\d+)")
_RE_MATRIX_N  = re.compile(r"^###\s+5\.(\d+)")
_RE_PLO_HDR   = re.compile(r"^###\s+(PLO\d+)")
_RE_PLO_DESC  = re.compile(r"^\*\*Mô tả:\*\*\s*(.*)")
_RE_PI_CODE   = re.compile(r"^PI\d+\.\d+$")
_RE_COURSE_CD = re.compile(r"^(FIT\d+|CSC\d+|IS0\d+)$")

_MATRIX_PROG: Dict[str, str] = {"1": "CNTT", "2": "HTTT", "3": "KHMT"}


def _split_pipe(line: str) -> List[str]:
    """Split a markdown table row on '|' and strip each cell."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _parse_irma_col(irma_str: str) -> Dict[str, str]:
    """Parse 'PI4.1:MA, PI4.2:R, ...' → {'PI4.1': 'MA', 'PI4.2': 'R', ...}"""
    out: Dict[str, str] = {}
    for token in irma_str.split(","):
        token = token.strip()
        if ":" in token:
            pi, lvl = token.split(":", 1)
            out[pi.strip()] = lvl.strip()
    return out


# ─── Main parser ─────────────────────────────────────────────────────────────

def _parse(path: Path) -> Dict[str, Dict]:
    """
    Parse KB_PLO_PI_Matrix_1.md into per-program dicts.

    Sections in the MD file:
      PHẦN 1  — shared PLO/PI (PLO1,2,3,7,8,9,12) used by all 3 programs
      PHẦN 2  — CNTT-specific PLO/PI (PLO4,5,6,10,11)
      PHẦN 3  — HTTT-specific PLO/PI
      PHẦN 4  — KHMT-specific PLO/PI
      PHẦN 5  — HP × PI × IRMA matrices
        ### 5.1  CNTT course matrix
        ### 5.2  HTTT course matrix
        ### 5.3  KHMT course matrix
      PHẦN 6  — quick lookup (ignored)
    """
    shared_plo: Dict[str, str] = {}
    shared_pi:  Dict[str, Dict[str, str]] = {}
    prog_plo:   Dict[str, Dict[str, str]]            = {"CNTT": {}, "HTTT": {}, "KHMT": {}}
    prog_pi:    Dict[str, Dict[str, Dict[str, str]]] = {"CNTT": {}, "HTTT": {}, "KHMT": {}}
    course_map: Dict[str, Dict[str, Dict[str, str]]] = {"CNTT": {}, "HTTT": {}, "KHMT": {}}

    section  = ""   # SHARED | PROG | MATRIX | MATRIX_CNTT | MATRIX_HTTT | MATRIX_KHMT | DONE
    cur_prog = ""
    cur_plo  = ""

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        # ── Top-level section header (## PHẦN N) ──────────────────────────────
        m = _RE_SECTION.match(line)
        if m:
            n = m.group(1)
            cur_plo = ""
            if   n == "1": section, cur_prog = "SHARED", ""
            elif n == "2": section, cur_prog = "PROG",   "CNTT"
            elif n == "3": section, cur_prog = "PROG",   "HTTT"
            elif n == "4": section, cur_prog = "PROG",   "KHMT"
            elif n == "5": section, cur_prog = "MATRIX", ""
            else:          section           = "DONE"
            continue

        if section == "DONE":
            continue

        # ── Matrix sub-section header (### 5.1 — CNTT) ───────────────────────
        if section.startswith("MATRIX"):
            m = _RE_MATRIX_N.match(line)
            if m:
                prog = _MATRIX_PROG.get(m.group(1), "")
                section = f"MATRIX_{prog}" if prog else "MATRIX"
                continue

        # ── PLO header (### PLO4) ─────────────────────────────────────────────
        if section in ("SHARED", "PROG"):
            m = _RE_PLO_HDR.match(line)
            if m:
                cur_plo = m.group(1)
                continue

        # ── PLO description ───────────────────────────────────────────────────
        if section in ("SHARED", "PROG") and cur_plo:
            m = _RE_PLO_DESC.match(line)
            if m:
                desc = m.group(1).rstrip(".")
                if section == "SHARED":
                    shared_plo[cur_plo] = desc
                else:
                    prog_plo[cur_prog][cur_plo] = desc
                continue

        # ── PI table row (| PI1.1 | description |) ───────────────────────────
        if section in ("SHARED", "PROG") and cur_plo and line.startswith("|"):
            parts = _split_pipe(line)
            if len(parts) >= 2 and _RE_PI_CODE.match(parts[0]):
                pi_code, pi_desc = parts[0], parts[1]
                if section == "SHARED":
                    shared_pi.setdefault(cur_plo, {})[pi_code] = pi_desc
                else:
                    prog_pi[cur_prog].setdefault(cur_plo, {})[pi_code] = pi_desc
            continue  # skip header/separator rows too

        # ── Course IRMA row (| FIT3001 | Course name | PI2.1:I, ... |) ────────
        if section.startswith("MATRIX_") and line.startswith("|"):
            parts = _split_pipe(line)
            if len(parts) >= 3 and _RE_COURSE_CD.match(parts[0]):
                prog    = section[len("MATRIX_"):]
                pi_irma = _parse_irma_col(parts[2])
                if pi_irma:
                    course_map[prog][parts[0]] = pi_irma

    # ── Assemble per-program data ─────────────────────────────────────────────
    return {
        prog: {
            "plo":        {**shared_plo, **prog_plo[prog]},
            "pi":         {**shared_pi,  **prog_pi[prog]},
            "course_map": course_map[prog],
        }
        for prog in ("CNTT", "HTTT", "KHMT")
    }


# ─── Load once at import ──────────────────────────────────────────────────────

_KB_FILE: Path           = _find_kb_file()
_DATA:    Dict[str, Dict] = _parse(_KB_FILE)


# ─── Internal helper ──────────────────────────────────────────────────────────

def _prog(program: str) -> str:
    p = (program or "KHMT").upper().strip()
    return p if p in _DATA else "KHMT"


# ─── Public API ───────────────────────────────────────────────────────────────

def get_pi_list(program: str) -> List[str]:
    """All PI codes for *program* in definition order (as in the KB file)."""
    codes: List[str] = []
    for pis in _DATA[_prog(program)]["pi"].values():
        codes.extend(pis.keys())
    return codes


def get_plo_description(plo_code: str, program: str) -> str:
    """Vietnamese description of *plo_code* for *program*."""
    return _DATA[_prog(program)]["plo"].get(plo_code, "")


def get_pi_description(pi_code: str, program: str) -> str:
    """Vietnamese description of *pi_code* for *program*."""
    for pis in _DATA[_prog(program)]["pi"].values():
        if pi_code in pis:
            return pis[pi_code]
    return ""


def get_course_irma(course_code: str, program: str) -> Dict[str, str]:
    """Official PI→IRMA mapping for *course_code* in *program*.

    Returns empty dict when the course is not in the official matrix.

    Examples
    --------
    >>> get_course_irma("CSC4007", "KHMT")
    {'PI5.2': 'M', 'PI5.3': 'M', 'PI6.3': 'R'}
    >>> get_course_irma("FIT4104", "CNTT")
    {'PI4.1': 'MA', 'PI4.2': 'MA', 'PI5.2': 'R', ...}
    >>> get_course_irma("FIT4303", "HTTT")
    {'PI5.2': 'M', 'PI5.4': 'MA', ...}
    """
    return dict(_DATA[_prog(program)]["course_map"].get(course_code, {}))


def get_plo_for_pi(pi_code: str, program: str) -> str:
    """PLO code that owns *pi_code* in *program*. Empty string if not found."""
    for plo_code, pis in _DATA[_prog(program)]["pi"].items():
        if pi_code in pis:
            return plo_code
    return ""
