"""
assessment.py - Assessment Plan + Rubric Generation Agent.

Generates a complete assessment plan with rubrics aligned to CLOs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from state import DCCTState, AgentStep, AssessmentItem

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "assessment.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an OBE assessment design expert. "
        "Create an assessment plan with weights summing to 1.0 and rubrics for each item. "
        "Respond in JSON array: "
        '[{"id":"A1","name":"Midterm Exam","type":"midterm","weight":0.3,'
        '"clo_ids":["CLO1","CLO2"],'
        '"rubric":{"excellent":"...","good":"...","satisfactory":"...","needs_improvement":"..."}}]'
    )


def assessment_node(state: DCCTState) -> dict:
    """Generate assessment plan and rubrics."""
    logger.info("[Assessment] Generating assessment plan.")

    clos = state.get("clos", [])
    clo_summary = "\n".join(f"- {c.id}: {c.description} [Bloom: {c.bloom_level}]" for c in clos)

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
    )

    user_content = (
        f"Course: {state.get('course_name')} — {state.get('credits')} credits\n"
        f"CLOs:\n{clo_summary}\n\n"
        "Design an assessment plan (quizzes, assignments, midterm, final, project) "
        "with CLO alignment and rubrics."
    )

    messages = [
        SystemMessage(content=_load_prompt()),
        HumanMessage(content=user_content),
    ]

    errors = list(state.get("errors", []))
    assessment_plan: list[AssessmentItem] = []

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()
        items: list[dict] = json.loads(raw)

        for item in items:
            assessment_plan.append(
                AssessmentItem(
                    id=item["id"],
                    name=item["name"],
                    type=item["type"],
                    weight=float(item["weight"]),
                    clo_ids=item.get("clo_ids", []),
                    rubric=item.get("rubric"),
                )
            )
        logger.info("[Assessment] Generated %d assessment items.", len(assessment_plan))
    except Exception as exc:
        logger.error("[Assessment] Parsing error: %s", exc)
        errors.append(f"[Assessment] Parsing error: {exc}")

    return {
        "assessment_plan": assessment_plan,
        "next_agent": AgentStep.SUPERVISOR,
        "current_step": AgentStep.ASSESSMENT,
        "errors": errors,
        "agent_logs": state.get("agent_logs", []) + [
            f"Assessment: {len(assessment_plan)} items"
        ],
    }
