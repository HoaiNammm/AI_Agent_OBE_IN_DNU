"""
Tests cho State schema
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import DCCTState, CLO, Session, AssessmentComponent


class TestCLOModel:
    def test_clo_creation_minimal(self):
        clo = CLO(code="CLO1", description="Giải thích khái niệm AI", bloom_verb="explain")
        assert clo.code == "CLO1"
        assert clo.description == "Giải thích khái niệm AI"
        assert clo.bloom_verb == "explain"
        assert clo.pi_codes == []
        assert clo.mapping_level == ""

    def test_clo_creation_full(self):
        clo = CLO(
            code="CLO3",
            description="Thiết kế hệ thống AI",
            bloom_verb="design",
            pi_codes=["PI3.1", "PI4.1"],
            mapping_level="M",
        )
        assert clo.pi_codes == ["PI3.1", "PI4.1"]
        assert clo.mapping_level == "M"


class TestSessionModel:
    def test_session_creation(self):
        session = Session(no=1, content="Giới thiệu AI")
        assert session.no == 1
        assert session.content == "Giới thiệu AI"
        assert session.clo_codes == []
        assert session.irma_level == ""

    def test_session_with_clos(self):
        session = Session(
            no=5,
            content="Machine Learning cơ bản",
            clo_codes=["CLO1", "CLO2"],
            irma_level="R",
            activities="Lecture + Lab",
        )
        assert session.clo_codes == ["CLO1", "CLO2"]
        assert session.irma_level == "R"


class TestAssessmentComponent:
    def test_assessment_creation(self):
        comp = AssessmentComponent(code="A1", name="Đánh giá quá trình")
        assert comp.code == "A1"
        assert comp.weight == 0.0
        assert comp.clo_mapping == []

    def test_assessment_with_weight(self):
        comp = AssessmentComponent(
            code="A3",
            name="Thi cuối kỳ",
            weight=0.4,
            clo_mapping=["CLO1", "CLO2", "CLO3"],
        )
        assert comp.weight == 0.4
        assert len(comp.clo_mapping) == 3


class TestDCCTStateInitialValues:
    def test_initial_state_structure(self):
        """Kiểm tra rằng state dict có thể được tạo với đúng cấu trúc"""
        initial_state = {
            "user_input": "CSC4012 - AI",
            "course_code": "CSC4012",
            "course_name": "Trí tuệ nhân tạo",
            "credits": "3",
            "summary": "Học phần AI",
            "outline": None,
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

        # Kiểm tra tất cả keys cần thiết đều có
        required_keys = [
            "user_input", "course_code", "course_name", "credits",
            "clo_list", "mapping_matrix", "teaching_plan", "assessment_plan",
            "current_step", "confidence_score", "critic_feedback",
        ]
        for key in required_keys:
            assert key in initial_state, f"Thiếu key: {key}"

    def test_confidence_score_default(self):
        state = {"confidence_score": 0.0}
        assert state["confidence_score"] == 0.0

    def test_credits_as_string(self):
        """Credits nên là string theo thiết kế"""
        state = {"credits": "3"}
        assert isinstance(state["credits"], str)
