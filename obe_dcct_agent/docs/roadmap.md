# Roadmap

## Phase 1 – MVP (Current)
- [x] Project scaffold and directory structure
- [x] Core Pydantic state models (`DCCTState`)
- [x] LangGraph pipeline with 5 specialist agents
- [x] Rule-based OBE critic tool
- [x] Word document export via `python-docx`
- [x] Streamlit UI (basic)
- [x] RAG indexing + retrieval with Qdrant
- [x] Prompt files for all agents

## Phase 2 – Quality & Reliability
- [ ] Unit tests for all agents and tools
- [ ] Integration tests for the full pipeline
- [ ] Retry logic with exponential backoff
- [ ] Structured logging with correlation IDs
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker Compose for local deployment

## Phase 3 – Advanced Features
- [ ] Human-in-the-loop review step in Streamlit UI
- [ ] Multi-language support (Vietnamese / English toggle)
- [ ] Batch processing (multiple courses at once)
- [ ] PLO library management (import/export PLO sets)
- [ ] PDF export option
- [ ] DCCT version history and diff view

## Phase 4 – Production
- [ ] Authentication (lecturer accounts)
- [ ] PostgreSQL persistence for DCCT history
- [ ] Admin dashboard for department heads
- [ ] Integration with university LMS (e.g., Moodle)
- [ ] Scheduled re-validation against updated OBE standards
