"""
frontend/components/input_form.py - Streamlit input form for course information.
"""

from __future__ import annotations

import streamlit as st


def render_input_form() -> dict | None:
    """
    Render the course information input form.

    Returns:
        A dict with form data if submitted, otherwise None.
    """
    with st.form("dcct_form"):
        st.subheader("Thông tin học phần")

        col1, col2 = st.columns(2)

        with col1:
            course_name = st.text_input(
                "Tên học phần *",
                placeholder="Ví dụ: Lập Trình Hướng Đối Tượng",
            )
            course_code = st.text_input(
                "Mã học phần *",
                placeholder="Ví dụ: CSE301",
            )

        with col2:
            credits = st.selectbox(
                "Số tín chỉ *",
                options=[1, 2, 3, 4],
                index=2,
            )
            department = st.text_input(
                "Khoa / Bộ môn",
                placeholder="Ví dụ: Khoa Công Nghệ Thông Tin",
            )

        raw_input = st.text_area(
            "Mô tả thêm (tuỳ chọn)",
            placeholder="Nhập thêm thông tin về nội dung, yêu cầu đặc biệt...",
            height=100,
        )

        submitted = st.form_submit_button("🚀 Tạo DCCT", type="primary")

    if submitted:
        if not course_name.strip():
            st.error("Vui lòng nhập tên học phần.")
            return None
        if not course_code.strip():
            st.error("Vui lòng nhập mã học phần.")
            return None
        return {
            "course_name": course_name.strip(),
            "course_code": course_code.strip(),
            "credits": int(credits),
            "department": department.strip(),
            "raw_input": raw_input.strip(),
        }

    return None
