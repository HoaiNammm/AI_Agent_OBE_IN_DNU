"""
Tests cho Supervisor Agent (logic thuần, không cần LLM)
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.supervisor import supervisor_node, STEP_SEQUENCE, MAX_RETRIES


class TestSupervisorRouting:
    def _make_state(self, current_step, critic_feedback=None, retry_counts=None):
        return {
            "current_step": current_step,
            "critic_feedback": critic_feedback or [],
            "retry_counts": retry_counts or {},
        }

    # ---- First pass routing ----
    def test_initial_state_routes_to_understand(self):
        state = self._make_state("understand")
        result = supervisor_node(state)
        assert result["current_step"] == "understand"

    def test_mapping_routes_to_mapping(self):
        state = self._make_state("mapping")
        result = supervisor_node(state)
        assert result["current_step"] == "mapping"

    def test_all_step_names_route_correctly(self):
        for step in STEP_SEQUENCE:
            state = self._make_state(step)
            result = supervisor_node(state)
            assert result["current_step"] == step

    # ---- After completion (done markers) ----
    def test_understand_done_advances_to_mapping(self):
        state = self._make_state(
            "understand_done",
            critic_feedback=[{"step": "understand", "passed": True}]
        )
        result = supervisor_node(state)
        assert result["current_step"] == "mapping"

    def test_mapping_done_advances_to_teaching_plan(self):
        state = self._make_state(
            "mapping_done",
            critic_feedback=[{"step": "mapping", "passed": True}]
        )
        result = supervisor_node(state)
        assert result["current_step"] == "teaching_plan"

    def test_teaching_plan_done_advances_to_assessment(self):
        state = self._make_state(
            "teaching_plan_done",
            critic_feedback=[{"step": "teaching_plan", "passed": True}]
        )
        result = supervisor_node(state)
        assert result["current_step"] == "assessment"

    def test_assessment_done_advances_to_final_validator(self):
        state = self._make_state(
            "assessment_done",
            critic_feedback=[{"step": "assessment", "passed": True}]
        )
        result = supervisor_node(state)
        assert result["current_step"] == "final_validator"

    # ---- Retry logic ----
    def test_critic_fail_triggers_retry(self):
        state = self._make_state(
            "understand_done",
            critic_feedback=[{"step": "understand", "passed": False}],
            retry_counts={}
        )
        result = supervisor_node(state)
        assert result["current_step"] == "understand"
        assert result["retry_counts"]["understand"] == 1

    def test_retry_count_increments(self):
        state = self._make_state(
            "understand_done",
            critic_feedback=[{"step": "understand", "passed": False}],
            retry_counts={"understand": 1}
        )
        result = supervisor_node(state)
        assert result["current_step"] == "understand"
        assert result["retry_counts"]["understand"] == 2

    def test_max_retries_exceeded_advances_anyway(self):
        """Sau MAX_RETRIES lần retry, vẫn tiến tới bước tiếp."""
        state = self._make_state(
            "understand_done",
            critic_feedback=[{"step": "understand", "passed": False}],
            retry_counts={"understand": MAX_RETRIES}
        )
        result = supervisor_node(state)
        assert result["current_step"] == "mapping"  # Advance despite failure

    def test_no_critic_feedback_advances(self):
        """Không có critic feedback → tiến tới bước tiếp theo."""
        state = self._make_state("understand_done", critic_feedback=[])
        result = supervisor_node(state)
        assert result["current_step"] == "mapping"

    # ---- Edge cases ----
    def test_unknown_step_resets_to_understand(self):
        state = self._make_state("invalid_step_xyz")
        result = supervisor_node(state)
        assert result["current_step"] == "understand"

    def test_last_step_done_goes_to_final_validator(self):
        """assessment_done → final_validator (cuối sequence)"""
        state = self._make_state(
            "assessment_done",
            critic_feedback=[{"step": "assessment", "passed": True}]
        )
        result = supervisor_node(state)
        assert result["current_step"] == "final_validator"
