"""
state.py - DCCTState definition and all Pydantic models used across the pipeline.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Optional
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


# ── Enums ──────────────────────────────────────────────────────────────────────

class BloomLevel(str, Enum):
    """Bloom's Taxonomy cognitive levels."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class IRMAType(str, Enum):
    """IRMA activity types."""
    INSTRUCTION = "I"
    RESEARCH = "R"
    MENTORING = "M"
    ASSESSMENT = "A"


class AgentStep(str, Enum):
    """Pipeline steps / agent names."""
    SUPERVISOR = "supervisor"
    UNDERSTAND = "understand"
    MAPPING = "mapping"
    TEACHING_PLAN = "teaching_plan"
    ASSESSMENT = "assessment"
    VALIDATOR = "validator"
    END = "end"


# ── Sub-models ─────────────────────────────────────────────────────────────────

class CLO(BaseModel):
    """Course Learning Outcome."""
    id: str = Field(..., description="CLO identifier, e.g. 'CLO1'")
    description: str = Field(..., description="CLO description")
    bloom_level: BloomLevel = Field(..., description="Bloom's taxonomy level")
    verbs: list[str] = Field(default_factory=list, description="Action verbs used")


class PI(BaseModel):
    """Performance Indicator mapped from a CLO."""
    id: str = Field(..., description="PI identifier, e.g. 'PI1.1'")
    clo_id: str = Field(..., description="Parent CLO identifier")
    description: str = Field(..., description="PI description")


class PLO(BaseModel):
    """Program Learning Outcome."""
    id: str = Field(..., description="PLO identifier, e.g. 'PLO1'")
    description: str = Field(..., description="PLO description")
    pi_ids: list[str] = Field(default_factory=list, description="Linked PI identifiers")


class IRMAActivity(BaseModel):
    """Single IRMA-typed teaching activity."""
    type: IRMAType
    description: str
    duration_hours: float = Field(ge=0)


class TeachingWeek(BaseModel):
    """One teaching week in the dynamic teaching plan."""
    week: int = Field(ge=1)
    topic: str
    clo_ids: list[str] = Field(default_factory=list)
    activities: list[IRMAActivity] = Field(default_factory=list)
    lecture_hours: float = 0.0
    practice_hours: float = 0.0


class AssessmentItem(BaseModel):
    """Single assessment component."""
    id: str
    name: str
    type: str = Field(..., description="e.g. 'quiz', 'midterm', 'project', 'final'")
    weight: float = Field(ge=0.0, le=1.0)
    clo_ids: list[str] = Field(default_factory=list)
    rubric: Optional[dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Outcome of the final validator agent."""
    passed: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# ── Main State ─────────────────────────────────────────────────────────────────

class DCCTState(MessagesState):
    """
    Central LangGraph state shared by all agents in the DCCT pipeline.
    All fields are optional so partial updates work naturally.
    """

    # ── Input ──────────────────────────────────────────────────────────────────
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    credits: Optional[int] = None
    department: Optional[str] = None
    raw_input: Optional[str] = None          # Free-text input from the lecturer

    # ── Agent Routing ──────────────────────────────────────────────────────────
    next_agent: Optional[str] = None
    current_step: Optional[AgentStep] = None
    retry_count: int = 0
    max_retries: int = 3

    # ── CLO / PLO / PI ─────────────────────────────────────────────────────────
    clos: list[CLO] = Field(default_factory=list)
    plos: list[PLO] = Field(default_factory=list)
    pis: list[PI] = Field(default_factory=list)

    # ── Teaching Plan ──────────────────────────────────────────────────────────
    teaching_weeks: list[TeachingWeek] = Field(default_factory=list)

    # ── Assessment ─────────────────────────────────────────────────────────────
    assessment_plan: list[AssessmentItem] = Field(default_factory=list)

    # ── Validation ─────────────────────────────────────────────────────────────
    validation_result: Optional[ValidationResult] = None

    # ── RAG Context ────────────────────────────────────────────────────────────
    retrieved_context: Optional[str] = None

    # ── Output ─────────────────────────────────────────────────────────────────
    output_path: Optional[str] = None        # Path to generated DCCT Word file
    preview_text: Optional[str] = None       # Markdown preview for the UI

    # ── Human-in-the-loop ──────────────────────────────────────────────────────
    human_feedback: Optional[str] = None
    awaiting_human: bool = False

    # ── Errors / Logs ──────────────────────────────────────────────────────────
    errors: list[str] = Field(default_factory=list)
    agent_logs: list[str] = Field(default_factory=list)
