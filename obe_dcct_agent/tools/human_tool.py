"""
human_tool.py - Human-in-the-loop (optional interrupt mechanism).

When called, this tool pauses the pipeline and signals the Supervisor
to wait for human feedback before continuing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from state import DCCTState

logger = logging.getLogger(__name__)


def request_human_feedback(state: "DCCTState", question: str) -> dict:
    """
    Signal that human feedback is needed.

    In a Streamlit deployment this sets ``awaiting_human=True`` so the UI
    can display the question and collect the lecturer's response.

    Args:
        state: Current DCCTState.
        question: The question/prompt to show the human.

    Returns:
        Partial state update dict.
    """
    logger.info("[HumanTool] Requesting human feedback: %s", question)

    return {
        "awaiting_human": True,
        "human_feedback": None,
        "agent_logs": state.get("agent_logs", []) + [f"HumanTool: '{question}'"],
    }


def submit_human_feedback(state: "DCCTState", feedback: str) -> dict:
    """
    Accept human feedback and resume the pipeline.

    Args:
        state: Current DCCTState.
        feedback: Feedback text provided by the human.

    Returns:
        Partial state update dict.
    """
    logger.info("[HumanTool] Human feedback received.")
    return {
        "awaiting_human": False,
        "human_feedback": feedback,
        "agent_logs": state.get("agent_logs", []) + ["HumanTool: feedback received"],
    }
