# Architecture

## System Overview

The OBE DCCT Agent is a multi-agent AI pipeline built with LangGraph.
It transforms raw course information into a fully compliant DCCT document.

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│              LangGraph Pipeline              │
│                                             │
│  ┌──────────┐   ┌───────────┐               │
│  │Supervisor│──▶│ Understand│               │
│  └──────────┘   └─────┬─────┘               │
│       ▲               │                     │
│       │               ▼                     │
│       │         ┌───────────┐               │
│       │         │  Mapping  │               │
│       │         └─────┬─────┘               │
│       │               │                     │
│       │      ┌────────┴────────┐            │
│       │      ▼                 ▼            │
│       │ ┌──────────┐  ┌────────────┐        │
│       │ │Teaching  │  │Assessment  │        │
│       │ │  Plan    │  │   Agent    │        │
│       │ └────┬─────┘  └─────┬──────┘       │
│       │      └──────┬────────┘             │
│       │             ▼                       │
│       │       ┌───────────┐                │
│       └───────│ Validator │                │
│               └─────┬─────┘                │
└─────────────────────┼──────────────────────┘
                       │
                       ▼
                 Word Document
                 (DCCT.docx)
```

## Components

### Core Pipeline (`graph.py`)
- Built with LangGraph `StateGraph`
- All agents share `DCCTState` (Pydantic-typed dict)
- Supervisor uses conditional edges to route between agents

### State (`state.py`)
- `DCCTState` extends `MessagesState` for LLM message tracking
- Typed sub-models: `CLO`, `PI`, `PLO`, `TeachingWeek`, `AssessmentItem`, `ValidationResult`

### Agents (`agents/`)
| Agent | Responsibility |
|-------|---------------|
| Supervisor | Planning, routing, loop detection |
| Understand | CLO generation from course info + RAG context |
| Mapping | CLO → PI → PLO + IRMA classification |
| TeachingPlan | Week-by-week plan with IRMA activities |
| Assessment | Assessment plan + rubrics |
| Validator | OBE compliance check + confidence score |

### RAG (`rag/`)
- Qdrant vector database
- OpenAI `text-embedding-3-small` embeddings
- Context injected into the Understand agent

### Export (`export/`)
- `python-docx` library
- Fills official DCCT_Template.docx with generated content
- Falls back to blank document if template missing

### Frontend (`frontend/`)
- Streamlit multi-tab UI
- Human-in-the-loop support via `tools/human_tool.py`

## Data Flow

```
raw_input → [Understand] → CLOs
CLOs      → [Mapping]    → PIs + PLOs
CLOs+PLOs → [Teaching]   → TeachingWeeks
CLOs      → [Assessment] → AssessmentPlan
All       → [Validator]  → ValidationResult + output_path
```

## Security Notes
- API keys stored in `.env` (never committed)
- Qdrant API key optional for local deployments
- No user data persisted beyond the current session
