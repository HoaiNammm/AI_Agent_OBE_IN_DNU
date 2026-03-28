"""
mapping.py - CLO → PI → PLO + IRMA Mapping Agent.

Maps each generated CLO to Performance Indicators (PIs) and Program Learning
Outcomes (PLOs), then assigns IRMA activity types.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from state import DCCTState, AgentStep, PI, PLO

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "mapping.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an OBE curriculum mapping expert. "
        "Given a list of CLOs, generate Performance Indicators (PIs) for each CLO "
        "and map them to Program Learning Outcomes (PLOs). "
        "Respond in JSON: "
        '{"pis": [{"id":"PI1.1","clo_id":"CLO1","description":"..."}], '
        '"plos": [{"id":"PLO1","description":"...","pi_ids":["PI1.1"]}]}'
    )


def mapping_node(state: DCCTState) -> dict:
    """Map CLOs → PIs → PLOs."""
    logger.info("[Mapping] Starting CLO → PI → PLO mapping.")

    clos = state.get("clos", [])
    if not clos:
        logger.warning("[Mapping] No CLOs found. Skipping mapping.")
        return {
            "next_agent": AgentStep.SUPERVISOR,
            "current_step": AgentStep.MAPPING,
            "errors": state.get("errors", []) + ["[Mapping] No CLOs to map."],
        }

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
    )

    clo_summary = "\n".join(
        f"- {c.id}: {c.description} [Bloom: {c.bloom_level}]" for c in clos
    )
    user_content = (
        f"Course: {state.get('course_name')} ({state.get('course_code')})\n"
        f"CLOs:\n{clo_summary}\n\n"
        "Generate PIs (2–3 per CLO) and map to PLOs."
    )

    messages = [
        SystemMessage(content=_load_prompt()),
        HumanMessage(content=user_content),
    ]

    errors = list(state.get("errors", []))
    pis: list[PI] = []
    plos: list[PLO] = []

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()
        data: dict = json.loads(raw)

        for item in data.get("pis", []):
            pis.append(PI(id=item["id"], clo_id=item["clo_id"], description=item["description"]))

        for item in data.get("plos", []):
            plos.append(PLO(id=item["id"], description=item["description"], pi_ids=item.get("pi_ids", [])))

        logger.info("[Mapping] Generated %d PIs and %d PLOs.", len(pis), len(plos))
    except Exception as exc:
        logger.error("[Mapping] Parsing error: %s", exc)
        errors.append(f"[Mapping] Parsing error: {exc}")

    return {
        "pis": pis,
        "plos": plos,
        "next_agent": AgentStep.SUPERVISOR,
        "current_step": AgentStep.MAPPING,
        "errors": errors,
        "agent_logs": state.get("agent_logs", []) + [
            f"Mapping: {len(pis)} PIs, {len(plos)} PLOs"
        ],
    }
