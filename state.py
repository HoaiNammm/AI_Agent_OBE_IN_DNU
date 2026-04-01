# state.py
from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import add_messages
from pydantic import BaseModel

class CLO(BaseModel):
    code: str
    description: str
    bloom_verb: str
    pi_codes: List[str] = []
    mapping_level: str = ""

class Session(BaseModel):
    no: int
    content: str
    clo_codes: List[str] = []
    irma_level: str = ""
    activities: str = ""
    assessment: str = ""

class AssessmentComponent(BaseModel):
    code: str
    name: str
    weight: float = 0.0
    clo_mapping: List[str] = []
    rubric: Dict = {}

class DCCTState(TypedDict):
    # Input
    user_input: str
    course_code: str
    course_name: str
    credits: str
    summary: str
    outline: Optional[str] = None

    # Processing
    extracted_info: Dict
    clo_list: List[CLO]
    mapping_matrix: List[Dict]
    teaching_plan: List[Session]      # Sẽ được xây dựng động
    assessment_plan: List[AssessmentComponent]
    rubrics: Dict

    # Control
    messages: Annotated[list, add_messages]
    current_step: str
    confidence_score: float = 0.0

    # Validation
    critic_feedback: List[Dict]
    retry_counts: Dict[str, int]

    # Preview & Human
    preview_data: Optional[Dict] = None
    needs_human_input: bool = False
    human_feedback: Optional[str] = None

    # Output
    final_dcct_data: Optional[Dict] = None
    export_ready: bool = False

    errors: List[str] = []
    warnings: List[str] = []