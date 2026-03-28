"""
frontend/app.py - Streamlit main application for the OBE DCCT Agent.

Run with:
    streamlit run frontend/app.py
"""

from __future__ import annotations

import sys
import os

# Allow imports from the project root when running from the frontend directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

from graph import graph
from state import DCCTState
from tools.preview_tool import generate_preview
from frontend.components.input_form import render_input_form
from frontend.components.result_view import render_result_view
from frontend.utils import get_download_bytes

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OBE DCCT Agent – DNU",
    page_icon="🎓",
    layout="wide",
)


def main() -> None:
    st.title("🎓 OBE DCCT Agent")
    st.caption("Xây dựng Đề Cương Chi Tiết học phần theo chuẩn OBE – Đại học Đà Nẵng")

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Hướng dẫn")
        st.markdown(
            """
            1. Điền thông tin học phần vào form.
            2. Nhấn **Tạo DCCT** để chạy pipeline AI.
            3. Xem bản preview và kiểm tra kết quả.
            4. Tải file Word DCCT về máy.
            """
        )
        st.divider()
        st.caption("Phiên bản 0.1.0 | MIT License")

    # ── Input Form ─────────────────────────────────────────────────────────────
    form_data = render_input_form()

    if form_data is None:
        st.info("Vui lòng điền đầy đủ thông tin học phần và nhấn **Tạo DCCT**.")
        return

    # ── Run pipeline ───────────────────────────────────────────────────────────
    with st.spinner("⏳ Đang chạy pipeline AI..."):
        initial_state: DCCTState = {
            "course_name": form_data["course_name"],
            "course_code": form_data["course_code"],
            "credits": form_data["credits"],
            "department": form_data["department"],
            "raw_input": form_data.get("raw_input", ""),
            "messages": [],
        }

        try:
            final_state = graph.invoke(initial_state)
        except Exception as exc:
            st.error(f"❌ Pipeline lỗi: {exc}")
            return

    # ── Results ────────────────────────────────────────────────────────────────
    st.success("✅ Pipeline hoàn tất!")

    # Generate and store preview
    preview_md = generate_preview(final_state)
    final_state["preview_text"] = preview_md

    render_result_view(final_state)

    # ── Download ───────────────────────────────────────────────────────────────
    output_path = final_state.get("output_path")
    if output_path and os.path.exists(output_path):
        file_bytes = get_download_bytes(output_path)
        st.download_button(
            label="📥 Tải DCCT (.docx)",
            data=file_bytes,
            file_name=os.path.basename(output_path),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    main()
