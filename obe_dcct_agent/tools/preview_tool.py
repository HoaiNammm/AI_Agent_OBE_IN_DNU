"""
preview_tool.py - Generate a Markdown preview of the DCCT for the lecturer.

This preview is shown in the Streamlit UI before the final Word export.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from state import DCCTState

logger = logging.getLogger(__name__)


def generate_preview(state: "DCCTState") -> str:
    """
    Build a Markdown-formatted preview of the current DCCT state.

    Returns:
        A Markdown string summarising the DCCT content.
    """
    lines: list[str] = []

    course_name = state.get("course_name", "N/A")
    course_code = state.get("course_code", "N/A")
    credits = state.get("credits", "N/A")
    department = state.get("department", "N/A")

    lines.append(f"# Đề Cương Chi Tiết: {course_name}")
    lines.append(f"**Mã học phần:** {course_code}  |  **Số tín chỉ:** {credits}  |  **Khoa:** {department}")
    lines.append("")

    # ── CLOs ──────────────────────────────────────────────────────────────────
    clos = state.get("clos", [])
    if clos:
        lines.append("## Chuẩn Đầu Ra Học Phần (CLOs)")
        for clo in clos:
            lines.append(f"- **{clo.id}** [{clo.bloom_level.upper()}]: {clo.description}")
        lines.append("")

    # ── PLOs ──────────────────────────────────────────────────────────────────
    plos = state.get("plos", [])
    if plos:
        lines.append("## Chuẩn Đầu Ra Chương Trình (PLOs)")
        for plo in plos:
            lines.append(f"- **{plo.id}**: {plo.description}  ← PIs: {', '.join(plo.pi_ids)}")
        lines.append("")

    # ── Teaching Plan ─────────────────────────────────────────────────────────
    weeks = state.get("teaching_weeks", [])
    if weeks:
        lines.append("## Kế Hoạch Giảng Dạy")
        lines.append("| Tuần | Chủ đề | CLOs | LT (h) | TH (h) |")
        lines.append("|------|--------|------|--------|--------|")
        for w in weeks:
            clo_str = ", ".join(w.clo_ids) if w.clo_ids else "—"
            lines.append(
                f"| {w.week} | {w.topic} | {clo_str} | {w.lecture_hours} | {w.practice_hours} |"
            )
        lines.append("")

    # ── Assessment Plan ────────────────────────────────────────────────────────
    assessment = state.get("assessment_plan", [])
    if assessment:
        lines.append("## Kế Hoạch Đánh Giá")
        lines.append("| ID | Hình thức | Trọng số | CLOs |")
        lines.append("|----|-----------|----------|------|")
        for a in assessment:
            clo_str = ", ".join(a.clo_ids) if a.clo_ids else "—"
            lines.append(f"| {a.id} | {a.name} ({a.type}) | {a.weight:.0%} | {clo_str} |")
        lines.append("")

    # ── Validation ────────────────────────────────────────────────────────────
    val = state.get("validation_result")
    if val:
        status = "✅ Đạt" if val.passed else "❌ Chưa đạt"
        lines.append(f"## Kết Quả Kiểm Tra OBE: {status}  (Điểm tin cậy: {val.confidence_score:.0%})")
        if val.issues:
            lines.append("**Vấn đề:**")
            for issue in val.issues:
                lines.append(f"- {issue}")
        if val.suggestions:
            lines.append("**Gợi ý:**")
            for sug in val.suggestions:
                lines.append(f"- {sug}")

    preview = "\n".join(lines)
    logger.info("[Preview] Generated preview (%d chars).", len(preview))
    return preview
