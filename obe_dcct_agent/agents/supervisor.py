"""
supervisor.py - Supervisor Agent: Planning & Decision routing.

The Supervisor reads the current DCCTState and decides which specialist
agent should run next (or signals END when the pipeline is complete).
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from state import DCCTState, AgentStep

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "supervisor.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are the Supervisor of an OBE DCCT generation pipeline. "
        "Decide which specialist agent to invoke next based on the current state. "
        "Reply with exactly one of: understand, mapping, teaching_plan, assessment, validator, end."
    )


def _build_status_summary(state: DCCTState) -> str:
    """Summarise what has already been completed."""
    parts = []
    parts.append(f"Course: {state.get('course_name')} ({state.get('course_code')}), {state.get('credits')} credits")
    parts.append(f"CLOs generated: {len(state.get('clos', []))}")
    parts.append(f"PLOs mapped: {len(state.get('plos', []))}")
    parts.append(f"Teaching weeks planned: {len(state.get('teaching_weeks', []))}")
    parts.append(f"Assessment items: {len(state.get('assessment_plan', []))}")
    val = state.get("validation_result")
    parts.append(f"Validation done: {val is not None}")
    return "\n".join(parts)


def supervisor_node(state: DCCTState) -> dict:
    """
    Supervisor agent node.
    Returns a partial state update with ``next_agent`` set.
    """
    logger.info("[Supervisor] Evaluating pipeline state...")

    # Fast-path: check if human is waiting for input
    if state.get("awaiting_human"):
        logger.info("[Supervisor] Awaiting human feedback — pausing.")
        return {"next_agent": AgentStep.END}

    # Fast-path: max retries exceeded
    if state.get("retry_count", 0) >= state.get("max_retries", 3):
        logger.warning("[Supervisor] Max retries reached. Ending pipeline.")
        return {"next_agent": AgentStep.END}

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
    )

    system_prompt = _load_prompt()
    status_summary = _build_status_summary(state)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=(
                f"Current pipeline status:\n{status_summary}\n\n"
                "Which agent should run next? "
                "Respond with exactly one word: understand, mapping, teaching_plan, "
                "assessment, validator, or end."
            )
        ),
    ]

    try:
        response = llm.invoke(messages)
        decision = response.content.strip().lower()
        logger.info("[Supervisor] Decision: %s", decision)
    except Exception as exc:
        logger.error("[Supervisor] LLM call failed: %s", exc)
        decision = AgentStep.END

    # Validate decision
    valid_steps = {s.value for s in AgentStep}
    if decision not in valid_steps:
        logger.warning("[Supervisor] Unknown decision '%s', defaulting to 'end'.", decision)
        decision = AgentStep.END

    return {
        "next_agent": decision,
        "current_step": AgentStep.SUPERVISOR,
        "agent_logs": state.get("agent_logs", []) + [f"Supervisor → {decision}"],
    }
