"""
utils/kb.py — Knowledge Base Layer 1 (Hardcode / Deterministic)

Đây là SINGLE SOURCE OF TRUTH cho tất cả rules OBE:
  - PLO / PI data (KHMT + HTTT + GENERIC)
  - PI domain classification (theory / design / practice / application / ...)
  - IRMA rules & Bloom↔IRMA mapping
  - Assessment rules & weights
  - Forbidden verbs (CLO quality check)

NGUYÊN TẮC QUAN TRỌNG:
  Tất cả agents gọi module này qua FUNCTION CALL trực tiếp.
  KHÔNG đưa PI/PLO rules vào Qdrant/RAG.
  Qdrant chỉ dùng cho prose context (TailieuMD, DCCT examples).

Lý do: cosine similarity không đảm bảo 100% trả về đúng rule cần thiết.
Nếu PI rule bị miss, agent mapping sai mà không có gì catch lại.
"""

from typing import Dict, List, Optional, Tuple

from utils.obe_utils import (
    # Generic (legacy)
    PLO_DATA,
    PI_DATA,
    # Shared
    IRMA_LEVELS,
    IRMA_BLOOM_MAP,
    DEFAULT_ASSESSMENT_WEIGHTS,
    BLOOM_LEVEL_VI,
    suggest_irma_for_bloom,
    get_plo_list_text_for_program,
    PROGRAM_DATA,
)


# ─────────────────────────────────────────────────────────────────────────────
# PI Domain Classification (deterministic, hand-curated)
# ─────────────────────────────────────────────────────────────────────────────

# Mỗi PLO group được gán một domain label ngắn.
# Agent mapping dùng để quyết định CLO nào nên map vào PI nào.

_PI_DOMAIN_KHMT: Dict[str, str] = {
    "PLO-CS01": "professional",   # ethics / compliance / citations
    "PLO-CS02": "theory",         # math / stats / model selection
    "PLO-CS03": "algorithms",     # algo design / complexity / testing
    "PLO-CS04": "experiment",     # experimental design / reproducibility
    "PLO-CS05": "ml_ai",          # ML/DL model building & evaluation
    "PLO-CS06": "systems",        # networks / OS / DB / security
    "PLO-CS07": "communication",  # writing / presentation / teamwork
    "PLO-CS08": "lifelong",       # self-learning / continuous improvement
}

_PI_DOMAIN_HTTT: Dict[str, str] = {
    "PLO-IS01": "professional",   # ethics / compliance / risk
    "PLO-IS02": "theory",         # foundational tech / tool usage
    "PLO-IS03": "analysis",       # requirements gathering / BRD/SRS
    "PLO-IS04": "design",         # process modelling / solution blueprint
    "PLO-IS05": "data",           # data modelling / governance
    "PLO-IS06": "application",    # BI / KPI / dashboards
    "PLO-IS07": "integration",    # system integration / architecture
    "PLO-IS08": "management",     # project planning / change management
}

# Bloom level ranges appropriate for each domain (inclusive)
DOMAIN_BLOOM_HINT: Dict[str, Tuple[int, int]] = {
    "professional":  (1, 4),
    "theory":        (1, 4),
    "algorithms":    (2, 5),
    "experiment":    (3, 6),
    "ml_ai":         (3, 6),
    "systems":       (2, 5),
    "communication": (2, 5),
    "lifelong":      (3, 6),
    "analysis":      (3, 6),
    "design":        (4, 6),
    "data":          (3, 6),
    "application":   (3, 6),
    "integration":   (3, 6),
    "management":    (3, 6),
}

# Forbidden CLO verbs (Bloom 1–2 weak verbs that shouldn't dominate ≥60% of CLOs)
FORBIDDEN_VERBS: List[str] = [
    "hiểu được", "biết được", "nắm được", "nhận dạng được",
    "mô tả được", "trình bày được", "liệt kê được", "nêu được",
    "biết", "hiểu", "nắm", "nhận biết", "mô tả", "trình bày", "liệt kê", "nêu",
]


# ─────────────────────────────────────────────────────────────────────────────
# Public API — PLO / PI lookup (deterministic)
# ─────────────────────────────────────────────────────────────────────────────

def get_plo_data(program: str) -> Dict[str, str]:
    """Trả về dict PLO code → description cho chương trình."""
    _p = (program or "GENERIC").upper()
    return PROGRAM_DATA.get(_p, PROGRAM_DATA.get("GENERIC", {})).get("plo", PLO_DATA)


def get_pi_data(program: str) -> Dict[str, Dict[str, str]]:
    """Trả về nested dict PLO_code → {PI_code → description} cho chương trình."""
    _p = (program or "GENERIC").upper()
    return PROGRAM_DATA.get(_p, PROGRAM_DATA.get("GENERIC", {})).get("pi", PI_DATA)


def get_all_pi_flat(program: str) -> Dict[str, str]:
    """
    Trả về flat dict {PI_code: description} cho toàn bộ chương trình.
    Dùng để validate PI code và lookup description.
    """
    result: Dict[str, str] = {}
    for _plo, pis in get_pi_data(program).items():
        result.update(pis)
    return result


def validate_pi_code(pi_code: str, program: str) -> bool:
    """
    Kiểm tra deterministic: PI code có thuộc chương trình không?
    Không dùng vector search. Đảm bảo 100%.
    """
    return pi_code in get_all_pi_flat(program)


def get_pi_plo(pi_code: str, program: str) -> Optional[Tuple[str, str]]:
    """
    Tra cứu (plo_code, pi_description) từ PI code.
    Trả về None nếu PI code không thuộc chương trình.
    """
    for plo_code, pis in get_pi_data(program).items():
        if pi_code in pis:
            return plo_code, pis[pi_code]
    return None


def get_pi_domain(plo_code: str, program: str) -> Optional[str]:
    """
    Trả về domain label (theory/design/practice/...) cho PLO group.
    Dùng để agent mapping biết loại CLO nào nên map vào đây.
    """
    _p = (program or "GENERIC").upper()
    if _p == "KHMT":
        return _PI_DOMAIN_KHMT.get(plo_code)
    if _p == "HTTT":
        return _PI_DOMAIN_HTTT.get(plo_code)
    return None


def get_bloom_range_for_domain(domain: str) -> Tuple[int, int]:
    """Bloom range phù hợp với domain. Dùng để validate CLO-PI alignment."""
    return DOMAIN_BLOOM_HINT.get(domain, (1, 6))


# ─────────────────────────────────────────────────────────────────────────────
# Public API — Prompt-ready text (deterministic)
# ─────────────────────────────────────────────────────────────────────────────

def get_pi_list_for_prompt(program: str) -> str:
    """
    Trả về PI list dạng text để inject thẳng vào system prompt mapping.
    Đây là dữ liệu cứng — LLM PHẢI chọn từ list này, không được bịa.

    Format mỗi dòng:
        PI-CS05.1 (PLO-CS05, domain=ml_ai, Bloom 3-6): <mô tả>
    """
    _p = (program or "GENERIC").upper()
    domain_map = _PI_DOMAIN_KHMT if _p == "KHMT" else (_PI_DOMAIN_HTTT if _p == "HTTT" else {})
    lines: List[str] = []

    for plo_code, pis in get_pi_data(program).items():
        domain = domain_map.get(plo_code, "general")
        bloom_lo, bloom_hi = get_bloom_range_for_domain(domain)
        plo_desc = get_plo_data(program).get(plo_code, "")
        lines.append(f"\n[{plo_code} | domain={domain} | Bloom {bloom_lo}-{bloom_hi}]")
        lines.append(f"  PLO: {plo_desc[:80]}")
        for pi_code, pi_desc in pis.items():
            lines.append(f"  {pi_code}: {pi_desc}")

    return "\n".join(lines)


def get_plo_list_for_prompt(program: str) -> str:
    """Trả về PLO list dạng text để inject vào prompt."""
    return get_plo_list_text_for_program(program)


def get_pi_validation_summary(program: str) -> str:
    """
    Sinh đoạn text tóm tắt rule validation cho Mapping Agent / Critic.
    Giải thích: CLO nào nên map vào PI nào dựa trên domain + Bloom.
    """
    _p = (program or "GENERIC").upper()
    domain_map = _PI_DOMAIN_KHMT if _p == "KHMT" else (_PI_DOMAIN_HTTT if _p == "HTTT" else {})

    lines = ["=== PI DOMAIN RULES (CỨNG — KHÔNG ĐƯỢC BỎ QUA) ==="]
    for plo_code, domain in domain_map.items():
        bloom_lo, bloom_hi = get_bloom_range_for_domain(domain)
        pis = get_pi_data(program).get(plo_code, {})
        pi_codes = ", ".join(pis.keys())
        lines.append(
            f"  {plo_code} (domain={domain}, Bloom {bloom_lo}-{bloom_hi}): {pi_codes}"
        )

    lines.append("")
    lines.append("Quy tắc mapping:")
    lines.append("  • CLO Bloom 1-3 + IRMA=I/R → ưu tiên PI domain=theory/professional/algorithms")
    lines.append("  • CLO Bloom 3-4 + IRMA=R/M → PI domain=experiment/practice/systems/data")
    lines.append("  • CLO Bloom 4-6 + IRMA=M/A → PI domain=ml_ai/design/application/integration")
    lines.append("  • CLO Bloom 5-6 + IRMA=A   → PI domain=experiment/design/management")
    lines.append("  • KHÔNG map CLO thực hành (Bloom≥4) vào PI domain=professional/theory")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Public API — IRMA rules (deterministic)
# ─────────────────────────────────────────────────────────────────────────────

def get_irma_rules() -> Dict:
    """Trả về IRMA levels, Bloom mapping và quy tắc progression."""
    return {
        "levels": IRMA_LEVELS,
        "bloom_map": IRMA_BLOOM_MAP,
        "progression_rule": "I → R → M → A theo thứ tự thời gian trong học phần",
        "note": "Mỗi CLO được introduce ở IRMA=I, sau đó reinforce/master ở các buổi sau",
    }


def suggest_irma(bloom_level: int) -> str:
    """Gợi ý IRMA từ Bloom level (deterministic mapping)."""
    return suggest_irma_for_bloom(bloom_level)


def get_irma_for_prompt() -> str:
    """Text mô tả IRMA rules để inject vào prompt."""
    lines = ["=== IRMA LEVELS ==="]
    for level, desc in IRMA_LEVELS.items():
        blooms = IRMA_BLOOM_MAP.get(level, [])
        bloom_names = [BLOOM_LEVEL_VI.get(b, str(b)) for b in blooms]
        lines.append(f"  {level}: {desc}")
        lines.append(f"     Bloom phù hợp: {', '.join(bloom_names)}")
    lines.append("")
    lines.append("Progression chuẩn OBE: I (tuần 1-3) → R (tuần 4-7) → M (tuần 8-11) → A (tuần 12+)")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Public API — Assessment rules (deterministic)
# ─────────────────────────────────────────────────────────────────────────────

def get_assessment_rules() -> Dict:
    """
    Trả về assessment rules và weights chuẩn DNU.
    Agents PHẢI dùng structure này, không được sáng tác weights mới.
    """
    return DEFAULT_ASSESSMENT_WEIGHTS.copy()


def get_assessment_for_prompt() -> str:
    """Text mô tả assessment rules để inject vào prompt."""
    lines = ["=== ASSESSMENT COMPONENTS (CỨNG) ==="]
    for code, info in DEFAULT_ASSESSMENT_WEIGHTS.items():
        lines.append(f"  {code} | {info['name']} | weight={info['weight']:.0%}")
        lines.append(f"     Format: {info['format']}")
        lines.append(f"     Criteria: {info['criteria_summary']}")
    lines.append("")
    lines.append("Quy tắc:")
    lines.append("  • A1: KHÔNG map CLO cụ thể (điểm danh/tham gia — không đo CLO)")
    lines.append("  • A2.1/A2.2: mỗi cái map ≥1 CLO, rubric có M1-M5 với threshold đo lường được")
    lines.append("  • A3: bao phủ tất cả CLO, tổng weight = 60%")
    lines.append("  • Tổng tất cả weight phải = 100%")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Public API — CLO quality rules (deterministic)
# ─────────────────────────────────────────────────────────────────────────────

def get_forbidden_verbs() -> List[str]:
    """Danh sách động từ yếu bị cấm dùng làm động từ chính trong CLO."""
    return FORBIDDEN_VERBS.copy()


def get_clo_quality_rules_for_prompt() -> str:
    """Text mô tả CLO quality rules để inject vào prompt."""
    forbidden_str = " | ".join(FORBIDDEN_VERBS[:8])  # first 8 for brevity
    lines = [
        "=== CLO QUALITY RULES (CỨNG) ===",
        f"  Động từ CẤM làm động từ chính: {forbidden_str} ...",
        "  Quy tắc Bloom: ≥ 60% CLO phải có Bloom ≥ 4 (Analyze/Evaluate/Create)",
        "  Cấu trúc CLO: [động từ hành vi] + [đối tượng kỹ thuật] + [ngữ cảnh/điều kiện]",
        "  Mỗi CLO dùng 1 động từ duy nhất — không viết 'biết và áp dụng'",
        "  Không lặp động từ giữa các CLO trong cùng học phần",
    ]
    return "\n".join(lines)


def check_clo_verb(verb: str) -> bool:
    """
    Kiểm tra deterministic: động từ CLO có nằm trong danh sách cấm không?
    True = hợp lệ (không bị cấm), False = bị cấm.
    """
    verb_l = verb.lower().strip()
    return not any(f in verb_l for f in FORBIDDEN_VERBS)


# ─────────────────────────────────────────────────────────────────────────────
# Public API — Composite context builder (for mapping agent)
# ─────────────────────────────────────────────────────────────────────────────

def build_mapping_kb_context(program: str) -> str:
    """
    Tổng hợp toàn bộ KB cần thiết cho Mapping Agent.
    Đây là hardcode context — KHÔNG qua RAG.

    Trả về text gồm:
      1. PI list đầy đủ với domain hints
      2. PI domain validation rules
      3. IRMA rules
    """
    return "\n\n".join([
        get_pi_list_for_prompt(program),
        get_pi_validation_summary(program),
        get_irma_for_prompt(),
    ])
