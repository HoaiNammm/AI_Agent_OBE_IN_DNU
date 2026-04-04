"""
Streamlit Frontend - Giao diện người dùng cho OBE DCCT Agent
"""

import asyncio
import os
import sys
from pathlib import Path

# Đảm bảo có thể import từ project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OBE DCCT Agent - ĐH Đà Nẵng",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLES
# ============================================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .section-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d6a9f;
        margin: 0.5rem 0;
    }
    .clo-item {
        background: white;
        padding: 0.7rem;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        margin: 0.3rem 0;
    }
    .confidence-high { color: #28a745; font-weight: bold; font-size: 1.2em; }
    .confidence-mid { color: #ffc107; font-weight: bold; font-size: 1.2em; }
    .confidence-low { color: #dc3545; font-weight: bold; font-size: 1.2em; }
    .metric-box {
        text-align: center;
        padding: 1rem;
        background: #e8f4f8;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 🎓 DNU - Khoa CNTT")
    st.markdown("### ⚙️ Cài đặt Agent")

    st.markdown("**API Keys:**")
    google_key = st.text_input("Google API Key", type="password",
                               value=os.getenv("GOOGLE_API_KEY", ""),
                               help="Gemini API key từ Google AI Studio")
    anthropic_key = st.text_input("Anthropic API Key", type="password",
                                  value=os.getenv("ANTHROPIC_API_KEY", ""),
                                  help="Claude API key từ Anthropic Console")

    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
    if anthropic_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key

    st.divider()
    st.markdown("**Thông tin:**")
    st.caption("🤖 LangGraph Agentic Workflow")
    st.caption("📚 OBE / AUN-QA Standard")
    st.caption("🏫 Khoa CNTT - ĐH Đà Nẵng")

# ============================================================
# MAIN HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1 style="margin:0">🎓 OBE DCCT Agent</h1>
    <p style="margin:0.3rem 0 0 0; opacity:0.9">
        Hệ thống tự động tạo Đề cương Chi tiết Học phần theo chuẩn Outcome-Based Education
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# INPUT FORM
# ============================================================

st.markdown("## 📝 Nhập thông tin học phần")

with st.form("course_input_form", clear_on_submit=False):
    col1, col2 = st.columns([1, 2])

    with col1:
        course_code = st.text_input(
            "Mã học phần *",
            placeholder="VD: CSC4012",
            help="Mã học phần theo quy định của trường",
        )
        credits = st.selectbox(
            "Số tín chỉ *",
            options=["2", "3", "4", "5"],
            index=1,
        )

    with col2:
        course_name = st.text_input(
            "Tên học phần *",
            placeholder="VD: Trí tuệ nhân tạo ứng dụng",
        )
        course_type = st.selectbox(
            "Loại học phần",
            options=["Lý thuyết + Thực hành", "Lý thuyết", "Thực hành"],
            index=0,
        )

    summary = st.text_area(
        "Mô tả / Tóm tắt học phần *",
        placeholder="Nhập mô tả ngắn về nội dung, mục tiêu học phần...",
        height=120,
    )

    outline = st.text_area(
        "Đề cương tham khảo (không bắt buộc)",
        placeholder="Dán đề cương cũ hoặc danh sách chủ đề chính...",
        height=100,
    )

    col3, col4 = st.columns(2)
    with col3:
        submitted = st.form_submit_button(
            "🚀 Tạo DCCT tự động",
            type="primary",
            use_container_width=True,
        )
    with col4:
        demo_btn = st.form_submit_button(
            "🎯 Chạy Demo",
            use_container_width=True,
        )

# ============================================================
# RUN AGENT
# ============================================================

def run_agent_sync(course_code, course_name, credits, summary, outline=None):
    """Wrapper đồng bộ để chạy async agent trong Streamlit."""
    from config import validate_config

    if not validate_config():
        return None, "Cần cấu hình ít nhất một API Key (Google hoặc Anthropic)"

    from graph import get_graph

    initial_state = {
        "user_input": f"{course_code} - {course_name}\n{summary}",
        "course_code": course_code,
        "course_name": course_name,
        "credits": credits,
        "summary": summary,
        "outline": outline,
        "extracted_info": {},
        "clo_list": [],
        "mapping_matrix": [],
        "teaching_plan": [],
        "assessment_plan": [],
        "rubrics": {},
        "messages": [],
        "current_step": "understand",
        "confidence_score": 0.0,
        "critic_feedback": [],
        "retry_counts": {},
        "preview_data": None,
        "needs_human_input": False,
        "human_feedback": None,
        "final_dcct_data": None,
        "export_ready": False,
        "errors": [],
        "warnings": [],
    }

    graph = get_graph()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            graph.ainvoke(initial_state, config={"configurable": {"thread_id": "1"}})
        )
        return result, None
    except Exception as e:
        return None, str(e)
    finally:
        loop.close()


if submitted or demo_btn:
    # Demo values nếu form trống
    if demo_btn:
        course_code = course_code or "CSC4012"
        course_name = course_name or "Trí tuệ nhân tạo ứng dụng"
        credits = credits or "3"
        summary = summary or (
            "Học phần giới thiệu các khái niệm và ứng dụng thực tế của Trí tuệ nhân tạo. "
            "Sinh viên học về machine learning, deep learning, xử lý ngôn ngữ tự nhiên và "
            "computer vision, với các bài thực hành sử dụng Python và các thư viện AI phổ biến."
        )

    # Validate input
    if not course_code or not course_name or not summary:
        st.error("⚠️ Vui lòng nhập đầy đủ: Mã học phần, Tên học phần và Mô tả!")
    else:
        # Progress tracking
        progress_container = st.empty()
        status_container = st.empty()

        with st.spinner("🤖 AI Agent đang xử lý..."):
            progress_bar = progress_container.progress(0, "Đang khởi động...")

            steps = [
                "Khởi tạo RAG system...",
                "Phân tích học phần và sinh CLO...",
                "Ánh xạ CLO → PI → PLO...",
                "Xây dựng kế hoạch giảng dạy...",
                "Thiết kế hệ thống đánh giá...",
                "Kiểm chứng và hoàn thiện...",
            ]

            # Simulate progress (thực tế sẽ update qua callback)
            import time
            for i, step in enumerate(steps):
                progress_bar.progress((i + 1) / len(steps), step)
                time.sleep(0.2)

            result, error = run_agent_sync(
                course_code, course_name, credits, summary,
                outline if outline else None
            )

        progress_container.empty()

        if error:
            st.error(f"❌ Lỗi: {error}")
        elif result:
            st.success("✅ Đã tạo DCCT thành công!")
            st.session_state["result"] = result
            st.session_state["course_code"] = course_code
            st.session_state["course_name"] = course_name


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "result" in st.session_state:
    result = st.session_state["result"]
    clo_list = result.get("clo_list", [])
    mapping_matrix = result.get("mapping_matrix", [])
    teaching_plan = result.get("teaching_plan", [])
    assessment_plan = result.get("assessment_plan", [])
    confidence = result.get("confidence_score", 0)
    errors = result.get("errors", [])

    st.divider()
    st.markdown("## 📊 Kết quả DCCT")

    # Metrics overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Confidence Score", f"{confidence:.1f}%",
                  delta="Tốt" if confidence >= 70 else "Cần cải thiện")
    with col2:
        st.metric("📚 Số CLO", len(clo_list))
    with col3:
        st.metric("📅 Số buổi học", len(teaching_plan))
    with col4:
        st.metric("📊 Cấu phần đánh giá", len(assessment_plan))

    # Errors/warnings
    if errors:
        with st.expander(f"⚠️ Cảnh báo ({len(errors)})", expanded=False):
            for e in errors:
                st.warning(e)

    # Tabs for different sections
    tabs = st.tabs(["🎯 CLO", "🗺️ Mapping", "📅 Kế hoạch giảng dạy", "📊 Đánh giá", "📄 Export"])

    # ---- Tab 1: CLO ----
    with tabs[0]:
        st.markdown("### Chuẩn đầu ra học phần (CLO)")
        if clo_list:
            for clo in clo_list:
                with st.expander(f"**{clo['code']}** - {clo['description'][:60]}..."):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Mô tả đầy đủ:** {clo['description']}")
                        st.markdown(f"**Động từ Bloom:** `{clo.get('bloom_verb', 'N/A')}`")
                        st.markdown(f"**Mức Bloom:** {clo.get('bloom_level_name', 'N/A')}")
                    with col_b:
                        st.markdown(f"**PI liên quan:** {', '.join(clo.get('pi_codes', [])) or 'N/A'}")
                        st.markdown(f"**Mức IRMA:** `{clo.get('mapping_level', 'N/A')}`")
        else:
            st.info("Chưa có CLO")

    # ---- Tab 2: Mapping ----
    with tabs[1]:
        st.markdown("### Ma trận ánh xạ CLO - PI - PLO")
        if mapping_matrix:
            import pandas as pd
            df_data = []
            for m in mapping_matrix:
                df_data.append({
                    "CLO": m.get("clo_code", ""),
                    "PI": m.get("pi_code", ""),
                    "PLO": m.get("plo_code", ""),
                    "IRMA": m.get("irma_level", ""),
                    "Bloom Level": m.get("bloom_level", ""),
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Chưa có mapping")

    # ---- Tab 3: Teaching Plan ----
    with tabs[2]:
        st.markdown("### Kế hoạch giảng dạy")
        if teaching_plan:
            import pandas as pd
            plan_data = []
            for s in teaching_plan:
                plan_data.append({
                    "Buổi": s.get("no", ""),
                    "Tuần": s.get("week", ""),
                    "Loại": s.get("type", ""),
                    "Nội dung": s.get("content", ""),
                    "CLO": ", ".join(s.get("clo_codes", [])),
                    "IRMA": s.get("irma_level", ""),
                    "Hoạt động": s.get("activities", ""),
                })
            df = pd.DataFrame(plan_data)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("Chưa có kế hoạch giảng dạy")

    # ---- Tab 4: Assessment ----
    with tabs[3]:
        st.markdown("### Hệ thống đánh giá")
        if assessment_plan:
            for a in assessment_plan:
                with st.expander(
                    f"**{a.get('code', '')}** - {a.get('name', '')} "
                    f"({a.get('weight', 0) * 100:.0f}%)"
                ):
                    st.markdown(f"**Mô tả:** {a.get('description', '')}")
                    st.markdown(f"**Hình thức:** {a.get('format', '')}")
                    st.markdown(f"**Tần suất:** {a.get('frequency', '')}")
                    st.markdown(f"**CLO đánh giá:** {', '.join(a.get('clo_mapping', []))}")

            # Pie chart trọng số
            import pandas as pd

            weight_data = {
                "Cấu phần": [a.get("code", "") for a in assessment_plan],
                "Trọng số": [a.get("weight", 0) * 100 for a in assessment_plan],
            }
            df_weight = pd.DataFrame(weight_data)
            st.bar_chart(df_weight.set_index("Cấu phần"))

        else:
            st.info("Chưa có hệ thống đánh giá")

    # ---- Tab 5: Export ----
    with tabs[4]:
        st.markdown("### Xuất file DCCT")

        col_export1, col_export2 = st.columns(2)

        with col_export1:
            if st.button("📄 Xuất file Word (.docx)", type="primary", use_container_width=True):
                with st.spinner("Đang tạo file Word..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        from export.word_generator import export_node
                        export_result = loop.run_until_complete(export_node(result))
                        if export_result.get("export_ready"):
                            filepath = export_result.get("export_path", "")
                            st.success(f"✅ Đã xuất: {Path(filepath).name}")
                            with open(filepath, "rb") as f:
                                st.download_button(
                                    "⬇️ Tải xuống DCCT.docx",
                                    f.read(),
                                    file_name=Path(filepath).name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                )
                        else:
                            st.error("Lỗi xuất file. Xem logs để biết thêm chi tiết.")
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
                    finally:
                        loop.close()

        with col_export2:
            if st.button("📋 Xuất JSON", use_container_width=True):
                import json
                final_data = result.get("final_dcct_data") or result
                json_str = json.dumps(final_data, ensure_ascii=False, indent=2)
                st.download_button(
                    "⬇️ Tải xuống DCCT.json",
                    json_str.encode("utf-8"),
                    file_name=f"DCCT_{st.session_state.get('course_code', 'export')}.json",
                    mime="application/json",
                )

        # Feedback section
        st.divider()
        st.markdown("### 💬 Phản hồi / Yêu cầu chỉnh sửa")
        feedback = st.text_area(
            "Nhập phản hồi để cải thiện DCCT:",
            placeholder="VD: CLO3 chưa đủ mức độ thực hành, cần thêm bài TH...",
            height=100,
        )
        if st.button("🔄 Cập nhật DCCT với phản hồi", use_container_width=True):
            if feedback:
                st.info("💡 Tính năng revision đang trong quá trình phát triển. "
                        "Hiện tại, vui lòng chỉnh sửa thông tin đầu vào và chạy lại.")
            else:
                st.warning("Vui lòng nhập phản hồi trước khi cập nhật.")

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.85em;">
    🎓 OBE DCCT Agent v1.0 | Khoa CNTT - ĐH Đà Nẵng | 
    Powered by LangGraph + Gemini/Claude
</div>
""", unsafe_allow_html=True)
