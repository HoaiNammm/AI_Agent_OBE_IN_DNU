"""
teaching_plan.py - Dynamic Teaching Plan Agent (theo tín chỉ + IRMA).

Generates a week-by-week teaching plan based on the number of credits,
CLOs, and IRMA activity distribution.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, CREDIT_HOURS_MAP
from state import DCCTState, AgentStep, TeachingWeek, IRMAActivity, IRMAType
from utils.obe_utils import calculate_total_weeks

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "teaching_plan.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an OBE teaching plan expert. Generate a week-by-week teaching plan. "
        "Each week must include a topic, linked CLO IDs, IRMA activities, "
        "and lecture/practice hours. "
        "Respond in JSON array: "
        '[{"week":1,"topic":"...","clo_ids":["CLO1"],'
        '"activities":[{"type":"I","description":"...","duration_hours":2}],'
        '"lecture_hours":2,"practice_hours":0}]'
    )


def teaching_plan_node(state: DCCTState) -> dict:
    """Generate the dynamic teaching plan."""
    logger.info("[TeachingPlan] Building teaching plan.")

    credits = state.get("credits", 3)
    hour_map = CREDIT_HOURS_MAP.get(credits, CREDIT_HOURS_MAP[3])
    total_weeks = calculate_total_weeks(credits)

    clos = state.get("clos", [])
    clo_summary = "\n".join(f"- {c.id}: {c.description}" for c in clos)

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
    )

    user_content = (
        f"Course: {state.get('course_name')} — {credits} credits\n"
        f"Total weeks: {total_weeks}\n"
        f"Lecture hours: {hour_map['lecture']}, Practice hours: {hour_map['practice']}\n"
        f"CLOs:\n{clo_summary}\n\n"
        f"Generate a {total_weeks}-week teaching plan with IRMA activities."
    )

    messages = [
        SystemMessage(content=_load_prompt()),
        HumanMessage(content=user_content),
    ]

    errors = list(state.get("errors", []))
    weeks: list[TeachingWeek] = []

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()
        week_data: list[dict] = json.loads(raw)

        for item in week_data:
            activities = []
            for act in item.get("activities", []):
                try:
                    irma_type = IRMAType(act["type"])
                except ValueError:
                    irma_type = IRMAType.INSTRUCTION
                activities.append(
                    IRMAActivity(
                        type=irma_type,
                        description=act.get("description", ""),
                        duration_hours=float(act.get("duration_hours", 1)),
                    )
                )
            weeks.append(
                TeachingWeek(
                    week=item["week"],
                    topic=item["topic"],
                    clo_ids=item.get("clo_ids", []),
                    activities=activities,
                    lecture_hours=float(item.get("lecture_hours", 0)),
                    practice_hours=float(item.get("practice_hours", 0)),
                )
            )
        logger.info("[TeachingPlan] Generated %d weeks.", len(weeks))
    except Exception as exc:
        logger.error("[TeachingPlan] Parsing error: %s", exc)
        errors.append(f"[TeachingPlan] Parsing error: {exc}")

    return {
        "teaching_weeks": weeks,
        "next_agent": AgentStep.SUPERVISOR,
        "current_step": AgentStep.TEACHING_PLAN,
        "errors": errors,
        "agent_logs": state.get("agent_logs", []) + [
            f"TeachingPlan: {len(weeks)} weeks generated"
        ],
    }
