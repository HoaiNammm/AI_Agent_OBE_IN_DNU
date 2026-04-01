# OBE DCCT Agent

**Hệ thống True Agentic Workflow tự động tạo Đề cương Chi tiết Học phần (DCCT) theo chuẩn Outcome-Based Education (OBE)**

Dự án được phát triển dành riêng cho Khoa Công nghệ Thông tin, giúp chuẩn hóa việc xây dựng đề cương học phần với khả năng mapping thông minh, kế hoạch giảng dạy động và cơ chế tự kiểm chứng cao.

---

## ✨ Tính năng chính

- Tự động sinh và tinh chỉnh **CLO** theo thang Bloom Taxonomy
- Ánh xạ thông minh **CLO → PI → PLO** kèm mức độ **I/R/M/A**
- Xây dựng **kế hoạch giảng dạy động** (dựa theo số tín chỉ, phân bổ LT/TH và mức IRMA)
- Thiết kế hệ thống đánh giá (**A1, A2.1, A2.2, A3**) và Rubric tự động
- Cơ chế **tự kiểm chứng** mạnh mẽ qua nhiều lớp Critic Agent
- **Preview Mode** thông minh trước khi xuất file (giảng viên xem & xác nhận)
- Xuất file **DCCT Word** theo đúng template chính thức của trường

---

## 🛠 Công nghệ sử dụng

- **Agent Orchestration**: LangGraph
- **LLM**: Gemini 1.5 Pro (thử nghiệm) + Claude 4.6 Sonnet (reasoning mạnh)
- **RAG & Vector DB**: Qdrant + Gemini Embeddings
- **Output**: python-docx
- **UI**: Streamlit (đang phát triển)
- **State Management**: Pydantic + LangGraph Checkpoint

---

## 📁 Cấu trúc dự án

```markdown
obe_dcct_agent/
├── main.py                  # Entry point
├── config.py                # Cấu hình API keys, models
├── state.py                 # DCCTState schema
├── graph.py                 # LangGraph workflow
│
├── agents/                  # Các Agent chuyên biệt
├── tools/                   # Critic, Preview, Human tools
├── rag/                     # Qdrant + Retriever
├── export/                  # Word file generator
├── prompts/                 # System prompts
├── utils/                   # Helper & OBE utilities
├── templates/               # DCCT_Template.docx
├── frontend/                # Streamlit UI
├── tests/                   # Unit & Integration tests
├── logs/                    # Log files
├── output/                  # Generated DCCT files
└── docs/                    # Tài liệu dự án

## Hướng dẫn cài đặt và chạy

1. git clone https://github.com/HoaiNammm/AI_Agent_OBE_IN_DNU

cd AI_Agent_OBE_IN_DNU

2. python -m venv venv
 - venv\Scripts\activate
 pip install -r requirements.txt

