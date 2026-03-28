"""
obe_utils.py - OBE-specific logic: IRMA calculator, Bloom verbs, hour calculations.
"""

from __future__ import annotations

from config import CREDIT_HOURS_MAP, IRMA_WEIGHTS

# ── Bloom's Taxonomy ───────────────────────────────────────────────────────────

BLOOM_VERBS: dict[str, list[str]] = {
    "remember": [
        "define", "list", "recall", "identify", "name", "recognize",
        "state", "match", "label", "memorize",
    ],
    "understand": [
        "explain", "describe", "summarize", "classify", "interpret",
        "paraphrase", "illustrate", "compare", "discuss", "predict",
    ],
    "apply": [
        "implement", "use", "demonstrate", "solve", "calculate",
        "execute", "apply", "operate", "practice", "sketch",
    ],
    "analyze": [
        "compare", "differentiate", "examine", "break down", "investigate",
        "distinguish", "attribute", "organize", "deconstruct", "outline",
    ],
    "evaluate": [
        "assess", "justify", "critique", "recommend", "judge",
        "argue", "defend", "prioritize", "appraise", "select",
    ],
    "create": [
        "design", "develop", "construct", "produce", "formulate",
        "plan", "compose", "build", "generate", "invent",
    ],
}


def get_bloom_verb_suggestions(level: str) -> list[str]:
    """Return suggested action verbs for the given Bloom level."""
    return BLOOM_VERBS.get(level.lower(), [])


def detect_bloom_level(description: str) -> str:
    """
    Heuristically detect the Bloom level from a CLO description by
    scanning for known action verbs.

    Returns the detected level string or 'understand' as default.
    """
    desc_lower = description.lower()
    # Check from highest to lowest so we return the most complex match
    for level in ["create", "evaluate", "analyze", "apply", "understand", "remember"]:
        for verb in BLOOM_VERBS[level]:
            if verb in desc_lower:
                return level
    return "understand"


# ── Credit / Hour Calculations ─────────────────────────────────────────────────

WEEKS_PER_SEMESTER = 15


def calculate_total_weeks(credits: int) -> int:
    """Return the standard number of teaching weeks for a given credit count."""
    return WEEKS_PER_SEMESTER


def calculate_contact_hours(credits: int) -> dict[str, int]:
    """
    Return total lecture and practice hours for a credit count.

    Falls back to the 3-credit mapping for unknown credit values.
    """
    return CREDIT_HOURS_MAP.get(credits, CREDIT_HOURS_MAP[3])


def calculate_irma_distribution(total_hours: float) -> dict[str, float]:
    """
    Calculate recommended IRMA hours given the total contact hours.

    Returns a dict with keys I, R, M, A.
    """
    return {
        activity_type: round(total_hours * weight, 1)
        for activity_type, weight in IRMA_WEIGHTS.items()
    }


# ── Assessment Validation ──────────────────────────────────────────────────────

def validate_weight_sum(weights: list[float], tolerance: float = 0.01) -> bool:
    """Return True if the assessment weights sum to approximately 1.0."""
    return abs(sum(weights) - 1.0) <= tolerance


def clo_coverage_matrix(
    clos: list, assessment_items: list
) -> dict[str, list[str]]:
    """
    Build a CLO → [assessment IDs] coverage matrix.

    Args:
        clos: List of CLO objects (with .id attribute).
        assessment_items: List of AssessmentItem objects (with .clo_ids and .id).

    Returns:
        dict mapping each CLO id to a list of assessment ids that cover it.
    """
    matrix: dict[str, list[str]] = {c.id: [] for c in clos}
    for item in assessment_items:
        for clo_id in item.clo_ids:
            if clo_id in matrix:
                matrix[clo_id].append(item.id)
    return matrix
