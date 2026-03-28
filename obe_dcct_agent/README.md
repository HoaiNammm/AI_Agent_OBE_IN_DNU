# OBE DCCT Agent

> AI Agent hỗ trợ xây dựng **Đề Cương Chi Tiết (DCCT)** học phần theo chuẩn **OBE (Outcome-Based Education)** tại Đại học Đà Nẵng.

---

## Tổng quan kiến trúc

```
User Input (Lecturer)
        │
        ▼
┌─────────────────┐
│   Supervisor    │  ← Planning & decision routing (LangGraph)
└────────┬────────┘
         │
    ┌────┴─────────────────────────────────────────┐
    │                                              │
    ▼                                              ▼
Understand Agent                          Mapping Agent
(Phân tích → CLOs)              (CLO → PI → PLO + IRMA mapping)
    │                                              │
    └───────────────────┬──────────────────────────┘
                        │
              ┌─────────┴──────────┐
              │                    │
    Teaching Plan Agent    Assessment Agent
    (Kế hoạch giảng dạy)   (Đánh giá + Rubric)
              │                    │
              └─────────┬──────────┘
                        │
                  Validator Agent
               (Kiểm tra OBE compliance)
                        │
                   Word Export
               (DCCT_Template.docx)
```

---

## Cài đặt

```bash
# 1. Clone và vào thư mục
cd obe_dcct_agent

# 2. Tạo virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Cấu hình biến môi trường
cp .env.example .env
# Chỉnh sửa .env với API keys của bạn
```

## Chạy CLI

```bash
python main.py \
  --course-name "Lập Trình Hướng Đối Tượng" \
  --course-code "CSE301" \
  --credits 3 \
  --department "Khoa Công Nghệ Thông Tin"
```

## Chạy API Server

```bash
uvicorn app:app --reload --port 8000
```

## Chạy Streamlit UI

```bash
streamlit run frontend/app.py
```

---

## Cấu trúc thư mục

```
obe_dcct_agent/
├── main.py            # CLI entry point
├── app.py             # FastAPI REST API
├── config.py          # API keys, models, thresholds
├── state.py           # DCCTState + Pydantic models
├── graph.py           # LangGraph orchestration
├── agents/            # Các agent chuyên biệt
├── tools/             # Tools gọi từ agent
├── rag/               # RAG & vector store
├── export/            # Sinh file Word DCCT
├── prompts/           # System prompts
├── templates/         # Template DCCT.docx
├── utils/             # Helper functions
├── frontend/          # Streamlit UI
├── docs/              # Tài liệu dự án
└── requirements.txt
```

---

## Môi trường phát triển

| Thành phần | Công nghệ |
|---|---|
| LLM | OpenAI GPT-4o |
| Orchestration | LangGraph |
| Vector DB | Qdrant |
| Embeddings | text-embedding-3-small |
| API Server | FastAPI |
| UI | Streamlit |
| Document Export | python-docx |

---

## Giấy phép

MIT License – xem file [LICENSE](LICENSE) để biết thêm chi tiết.
