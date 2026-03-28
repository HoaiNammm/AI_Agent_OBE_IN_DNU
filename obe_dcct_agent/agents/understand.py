"""
understand.py - Understand & CLO Generation Agent.

Analyses the course input and generates Course Learning Outcomes (CLOs)
aligned to Bloom's Taxonomy and OBE standards.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, MAX_CLO_COUNT, MIN_CLO_COUNT
from state import DCCTState, AgentStep, CLO, BloomLevel
from rag.retriever import retrieve_context

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "understand.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an OBE curriculum expert. Generate Course Learning Outcomes (CLOs) "
        f"for the given course. Provide between {MIN_CLO_COUNT} and {MAX_CLO_COUNT} CLOs. "
        "Each CLO must start with a Bloom's Taxonomy action verb and map to a cognitive level. "
        "Respond in JSON array format: "
        '[{"id":"CLO1","description":"...","bloom_level":"apply","verbs":["implement"]}]'
    )


def understand_node(state: DCCTState) -> dict:
    """Generate CLOs from course information."""
    logger.info("[Understand] Generating CLOs for course: %s", state.get("course_name"))

    # Retrieve relevant OBE context from RAG
    query = f"{state.get('course_name', '')} {state.get('raw_input', '')}"
    try:
        context = retrieve_context(query)
    except Exception as exc:
        logger.warning("[Understand] RAG retrieval failed: %s", exc)
        context = ""

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
    )

    system_prompt = _load_prompt()
    user_content = (
        f"Course name: {state.get('course_name')}\n"
        f"Course code: {state.get('course_code')}\n"
        f"Credits: {state.get('credits')}\n"
        f"Department: {state.get('department', '')}\n"
        f"Additional input: {state.get('raw_input', '')}\n"
    )
    if context:
        user_content += f"\nRelevant OBE guidelines:\n{context}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    errors = list(state.get("errors", []))
    clos: list[CLO] = []

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
            raw = raw.rstrip("`").strip()
        clo_data: list[dict] = json.loads(raw)
        for item in clo_data:
            bloom_raw = item.get("bloom_level", "understand").lower()
            try:
                bloom = BloomLevel(bloom_raw)
            except ValueError:
                bloom = BloomLevel.UNDERSTAND
            clos.append(
                CLO(
                    id=item["id"],
                    description=item["description"],
                    bloom_level=bloom,
                    verbs=item.get("verbs", []),
                )
            )
        logger.info("[Understand] Generated %d CLOs.", len(clos))
    except Exception as exc:
        logger.error("[Understand] Failed to parse CLOs: %s", exc)
        errors.append(f"[Understand] CLO parsing error: {exc}")

    return {
        "clos": clos,
        "retrieved_context": context,
        "next_agent": AgentStep.SUPERVISOR,
        "current_step": AgentStep.UNDERSTAND,
        "errors": errors,
        "agent_logs": state.get("agent_logs", []) + [f"Understand: generated {len(clos)} CLOs"],
    }
