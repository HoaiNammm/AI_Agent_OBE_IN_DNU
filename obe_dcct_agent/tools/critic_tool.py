"""
critic_tool.py - Self-critique & OBE rule validation.

Provides rule-based checks on the DCCTState before the LLM validator
is invoked, ensuring fast feedback on obvious issues.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from state import DCCTState

logger = logging.getLogger(__name__)


def run_critic(state: "DCCTState") -> list[str]:
    """
    Run deterministic OBE rule checks on the current state.

    Returns:
        A list of issue strings (empty if all checks pass).
    """
    issues: list[str] = []

    clos = state.get("clos", [])
    plos = state.get("plos", [])
    pis = state.get("pis", [])
    assessment = state.get("assessment_plan", [])
    weeks = state.get("teaching_weeks", [])
    credits = state.get("credits", 3)

    # ── CLO checks ─────────────────────────────────────────────────────────────
    if not clos:
        issues.append("No CLOs generated.")
    else:
        for clo in clos:
            if not clo.verbs:
                issues.append(f"{clo.id} has no action verbs.")
            if not clo.description.strip():
                issues.append(f"{clo.id} has an empty description.")

    # ── PLO / PI linkage ───────────────────────────────────────────────────────
    clo_ids = {c.id for c in clos}
    pi_ids = {p.id for p in pis}

    for pi in pis:
        if pi.clo_id not in clo_ids:
            issues.append(f"PI {pi.id} references unknown CLO {pi.clo_id}.")

    for plo in plos:
        orphan_pis = [pid for pid in plo.pi_ids if pid not in pi_ids]
        if orphan_pis:
            issues.append(f"PLO {plo.id} references unknown PIs: {orphan_pis}.")

    # ── Assessment weight sum ──────────────────────────────────────────────────
    if assessment:
        total_weight = sum(a.weight for a in assessment)
        if not (0.99 <= total_weight <= 1.01):
            issues.append(
                f"Assessment weights sum to {total_weight:.2f}, expected 1.00."
            )
        for item in assessment:
            orphan_clos = [cid for cid in item.clo_ids if cid not in clo_ids]
            if orphan_clos:
                issues.append(
                    f"Assessment item {item.id} references unknown CLOs: {orphan_clos}."
                )

    # ── Teaching weeks coverage ────────────────────────────────────────────────
    if weeks:
        covered_clos = {cid for w in weeks for cid in w.clo_ids}
        uncovered = clo_ids - covered_clos
        if uncovered:
            issues.append(f"CLOs not covered in any teaching week: {uncovered}.")

        total_lecture = sum(w.lecture_hours for w in weeks)
        total_practice = sum(w.practice_hours for w in weeks)
        logger.debug(
            "[Critic] lecture_hours=%.1f, practice_hours=%.1f",
            total_lecture,
            total_practice,
        )

    if issues:
        logger.warning("[Critic] Found %d issue(s): %s", len(issues), issues)
    else:
        logger.info("[Critic] All OBE rule checks passed.")

    return issues
