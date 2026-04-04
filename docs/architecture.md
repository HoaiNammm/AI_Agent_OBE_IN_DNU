# Kiến trúc hệ thống OBE DCCT Agent

## Tổng quan

OBE DCCT Agent là hệ thống **True Agentic Workflow** sử dụng LangGraph để tự động xây dựng Đề cương Chi tiết Học phần (DCCT) theo chuẩn OBE/AUN-QA.

## Sơ đồ kiến trúc

```
User Input (course_code, course_name, credits, summary)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                         │
│                                                               │
│   START ──► Supervisor ──► Understand ──► Critic ──┐         │
│                │  ▲                                │         │
│                │  └──────────────────────────────── │         │
│                ▼                                    ▼         │
│            Mapping ──► Critic ──► Supervisor ◄─────┘         │
│                                      │                        │
│                                      ▼                        │
│                               Teaching Plan ──► Critic        │
│                                      │                        │
│                                      ▼                        │
│                                 Assessment ──► Critic         │
│                                      │                        │
│                                      ▼                        │
│                              Final Validator                  │
│                                 │    │    │                   │
│                          ≥90%   │    │    │   <70%            │
│                                 ▼    ▼    ▼                   │
│                              Export Preview Supervisor        │
│                                 │                             │
└─────────────────────────────────┼─────────────────────────────┘
                                  ▼
                         DCCT Word File (.docx)
```

## Các Agent và chức năng

### 1. Supervisor Agent (`agents/supervisor.py`)
- **Loại**: Pure logic (không dùng LLM)
- **Chức năng**: Điều phối luồng workflow
- **Logic**:
  - Đọc `current_step` và `critic_feedback`
  - Quyết định tiến bước hay retry
  - Giới hạn retry: `MAX_RETRIES = 2` lần mỗi bước

### 2. Understand Agent (`agents/understand.py`)
- **LLM**: Gemini 1.5 Pro
- **Input**: course_code, course_name, credits, summary
- **Output**: `extracted_info`, `clo_list` (với Bloom taxonomy)
- **Prompt**: `prompts/understand_prompt.py`

### 3. Mapping Agent (`agents/mapping.py`)
- **LLM**: Claude 4.6 Sonnet
- **Input**: `clo_list`, RAG context (PLO/PI data)
- **Output**: `mapping_matrix` (CLO → PI → PLO + IRMA)
- **Prompt**: `prompts/mapping_prompt.py`

### 4. Teaching Plan Agent (`agents/teaching_plan.py`)
- **LLM**: Gemini 1.5 Pro
- **Input**: `clo_list`, `credits`, `mapping_matrix`
- **Output**: `teaching_plan` (kế hoạch buổi học động)
- **Tính toán**: `utils/obe_utils.py::calculate_sessions()`

### 5. Assessment Agent (`agents/assessment.py`)
- **LLM**: Claude 4.6 Sonnet
- **Input**: `clo_list`, `mapping_matrix`, `teaching_plan`
- **Output**: `assessment_plan` (A1/A2.1/A2.2/A3), `rubrics`

### 6. Final Validator Agent (`agents/validator.py`)
- **LLM**: Claude 4.6 Sonnet
- **Input**: Toàn bộ dữ liệu DCCT
- **Output**: `confidence_score` (0-100), `final_dcct_data`
- **Tiêu chí**: CLO Quality + Mapping Alignment + Teaching Coherence + Assessment Validity

### 7. Critic Tool (`tools/critic_tool.py`)
- **LLM**: Claude 4.6 Sonnet
- **Chức năng**: Review độc lập output của từng bước
- **Output**: `{passed: bool, score: int, issues: [], suggestions: []}`

### 8. Preview Tool (`tools/preview_tool.py`)
- **Loại**: Pure formatting (không LLM)
- **Chức năng**: Format DCCT để giảng viên xem trước

### 9. Word Generator (`export/word_generator.py`)
- **Thư viện**: `python-docx`
- **Output**: File `.docx` chuẩn với đầy đủ sections

## State Management

### DCCTState (`state.py`)
```
Input:     user_input, course_code, course_name, credits, summary, outline
Processing: extracted_info, clo_list, mapping_matrix, teaching_plan, assessment_plan, rubrics
Control:   messages, current_step, confidence_score
Validation: critic_feedback, retry_counts
Preview:   preview_data, needs_human_input, human_feedback
Output:    final_dcct_data, export_ready
Meta:      errors, warnings
```

## RAG System (`rag/`)

- **Backend**: Qdrant in-memory
- **Embeddings**: Gemini `models/embedding-001`
- **Dữ liệu**: PLO/PI/Bloom Taxonomy documents từ `utils/obe_utils.py`
- **Fallback**: Dữ liệu tĩnh khi Qdrant không khả dụng

## OBE Knowledge Base (`utils/obe_utils.py`)

### PLO (10 Program Learning Outcomes)
- PLO1-PLO10 chuẩn AUN-QA cho chương trình IT

### PI (Performance Indicators)
- 2-4 PI cho mỗi PLO (tổng ~25 PI)
- Mỗi PI đo lường được, gắn với PLO cha

### Bloom Taxonomy (6 levels)
- Verbs tiếng Việt + tiếng Anh cho mỗi mức

### IRMA Levels
- I (Introduce) ↔ Bloom 1-2
- R (Reinforce) ↔ Bloom 2-3
- M (Master) ↔ Bloom 3-4
- A (Apply) ↔ Bloom 4-6

## Hệ thống đánh giá

| Cấu phần | Tên | Trọng số mặc định |
|----------|-----|-------------------|
| A1 | Đánh giá quá trình | 10% |
| A2.1 | Kiểm tra giữa kỳ | 20% |
| A2.2 | Thực hành / Bài tập lớn | 30% |
| A3 | Thi cuối kỳ | 40% |

## Confidence Score

| Mức | Hành động |
|-----|-----------|
| ≥ 90% | Tự động xuất Word |
| 70-89% | Vào Preview Mode |
| < 70% | Quay về Supervisor, retry |

## Cài đặt và chạy

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Cấu hình API Keys
cp .env.example .env
# Chỉnh sửa .env với API keys thực

# 3. Chạy CLI
python main.py

# 4. Chạy Streamlit UI
streamlit run frontend/app.py

# 5. Chạy tests
pytest tests/ -v
```

## Cấu trúc thư mục

```
obe_dcct_agent/
├── main.py                 # CLI entry point
├── config.py               # Cấu hình API keys, models
├── state.py                # DCCTState TypedDict schema
├── graph.py                # LangGraph workflow definition
├── requirements.txt        # Python dependencies
├── .env.example            # Template cấu hình environment
│
├── agents/                 # 6 Specialist Agents
│   ├── supervisor.py       # Workflow orchestrator (pure logic)
│   ├── understand.py       # CLO generation (Gemini)
│   ├── mapping.py          # CLO→PI→PLO mapping (Claude)
│   ├── teaching_plan.py    # Session planning (Gemini)
│   ├── assessment.py       # Assessment design (Claude)
│   └── validator.py        # Quality validation (Claude)
│
├── tools/                  # Support tools
│   ├── critic_tool.py      # Independent reviewer (Claude)
│   └── preview_tool.py     # Preview formatter
│
├── rag/                    # RAG system
│   ├── index_builder.py    # Qdrant in-memory index
│   └── retriever.py        # Semantic retrieval
│
├── export/                 # Output generation
│   └── word_generator.py   # python-docx Word export
│
├── prompts/                # System prompts
│   ├── understand_prompt.py
│   ├── mapping_prompt.py
│   ├── teaching_plan_prompt.py
│   ├── assessment_prompt.py
│   ├── validator_prompt.py
│   └── critic_prompt.py
│
├── utils/                  # Utilities
│   ├── obe_utils.py        # OBE data (PLO/PI/Bloom/IRMA)
│   ├── llm_helper.py       # LLM factory & helpers
│   └── logger.py           # Structured logging
│
├── frontend/               # Streamlit UI
│   └── app.py
│
├── tests/                  # Unit tests
│   ├── test_obe_utils.py
│   ├── test_state.py
│   └── test_supervisor.py
│
├── templates/              # DCCT Word templates
├── output/                 # Generated DCCT files
├── logs/                   # Log files
└── docs/                   # Documentation
    └── architecture.md
```
