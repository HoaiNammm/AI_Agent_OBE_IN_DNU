"""
frontend/components/result_view.py - Streamlit result display component.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from state import DCCTState


def render_result_view(state: "DCCTState") -> None:
    """Render the pipeline results in the Streamlit UI."""

    tabs = st.tabs(["📋 Preview", "🎯 CLOs", "🗺️ Mapping", "📅 Teaching Plan", "📊 Assessment", "✅ Validation"])

    # ── Preview Tab ────────────────────────────────────────────────────────────
    with tabs[0]:
        preview = state.get("preview_text", "")
        if preview:
            st.markdown(preview)
        else:
            st.info("Chưa có bản preview.")

    # ── CLOs Tab ───────────────────────────────────────────────────────────────
    with tabs[1]:
        clos = state.get("clos", [])
        if clos:
            for clo in clos:
                with st.expander(f"**{clo.id}** — {clo.bloom_level.upper()}"):
                    st.write(clo.description)
                    st.caption(f"Động từ hành động: {', '.join(clo.verbs)}")
        else:
            st.info("Chưa có CLOs.")

    # ── Mapping Tab ────────────────────────────────────────────────────────────
    with tabs[2]:
        plos = state.get("plos", [])
        pis = state.get("pis", [])
        if plos or pis:
            if pis:
                st.subheader("Performance Indicators (PIs)")
                for pi in pis:
                    st.markdown(f"- **{pi.id}** ({pi.clo_id}): {pi.description}")
            if plos:
                st.subheader("Program Learning Outcomes (PLOs)")
                for plo in plos:
                    pi_list = ", ".join(plo.pi_ids) if plo.pi_ids else "—"
                    st.markdown(f"- **{plo.id}** [{pi_list}]: {plo.description}")
        else:
            st.info("Chưa có dữ liệu mapping.")

    # ── Teaching Plan Tab ──────────────────────────────────────────────────────
    with tabs[3]:
        weeks = state.get("teaching_weeks", [])
        if weeks:
            import pandas as pd
            rows = []
            for w in weeks:
                rows.append({
                    "Tuần": w.week,
                    "Chủ đề": w.topic,
                    "CLOs": ", ".join(w.clo_ids),
                    "LT (h)": w.lecture_hours,
                    "TH (h)": w.practice_hours,
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("Chưa có kế hoạch giảng dạy.")

    # ── Assessment Tab ─────────────────────────────────────────────────────────
    with tabs[4]:
        assessment = state.get("assessment_plan", [])
        if assessment:
            import pandas as pd
            rows = []
            for a in assessment:
                rows.append({
                    "ID": a.id,
                    "Hình thức": a.name,
                    "Loại": a.type,
                    "Trọng số": f"{a.weight:.0%}",
                    "CLOs": ", ".join(a.clo_ids),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            total_w = sum(a.weight for a in assessment)
            color = "green" if abs(total_w - 1.0) < 0.01 else "red"
            st.markdown(f"**Tổng trọng số:** :{color}[{total_w:.0%}]")
        else:
            st.info("Chưa có kế hoạch đánh giá.")

    # ── Validation Tab ─────────────────────────────────────────────────────────
    with tabs[5]:
        val = state.get("validation_result")
        if val:
            status_icon = "✅" if val.passed else "❌"
            st.metric("Trạng thái", f"{status_icon} {'Đạt' if val.passed else 'Chưa đạt'}")
            st.metric("Điểm tin cậy", f"{val.confidence_score:.0%}")

            if val.issues:
                st.subheader("Vấn đề")
                for issue in val.issues:
                    st.warning(issue)
            if val.suggestions:
                st.subheader("Gợi ý cải thiện")
                for sug in val.suggestions:
                    st.info(sug)
        else:
            st.info("Chưa có kết quả kiểm tra.")

        errors = state.get("errors", [])
        if errors:
            st.subheader("Lỗi hệ thống")
            for err in errors:
                st.error(err)
