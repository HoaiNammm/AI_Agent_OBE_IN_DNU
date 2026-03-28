"""
validator.py - Final Validator Agent + Confidence Score.

Validates the complete DCCT output against OBE rules and assigns
a confidence score. If the score is below the threshold, it signals
the Supervisor to retry specific agents.
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, MIN_CONFIDENCE_SCORE
from state import DCCTState, AgentStep, ValidationResult
from tools.critic_tool import run_critic
from export.word_generator import generate_word_document

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "validator.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an OBE compliance validator. "
        "Check the DCCT for: CLO completeness, Bloom's alignment, "
        "CLO-PI-PLO linkage, assessment weight sum = 1.0, and IRMA distribution. "
        "Respond in JSON: "
        '{"passed":true,"confidence_score":0.92,"issues":[],"suggestions":[]}'
    )


def validator_node(state: DCCTState) -> dict:
    """Validate the complete DCCT and optionally export to Word."""
    logger.info("[Validator] Starting validation.")

    # Run rule-based critic first
    critic_issues = run_critic(state)

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.0,  # deterministic for validation
    )

    clos = state.get("clos", [])
    plos = state.get("plos", [])
    assessment = state.get("assessment_plan", [])
    weeks = state.get("teaching_weeks", [])

    summary = (
        f"CLOs: {len(clos)}, PLOs: {len(plos)}, "
        f"Assessment items: {len(assessment)}, Teaching weeks: {len(weeks)}\n"
        f"Rule-based issues: {critic_issues}"
    )

    import json

    messages = [
        SystemMessage(content=_load_prompt()),
        HumanMessage(content=f"DCCT Summary:\n{summary}\n\nValidate and score."),
    ]

    errors = list(state.get("errors", []))
    validation_result: ValidationResult | None = None
    output_path: str | None = None

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()
        data: dict = json.loads(raw)

        all_issues = critic_issues + data.get("issues", [])
        validation_result = ValidationResult(
            passed=data.get("passed", False) and not critic_issues,
            confidence_score=float(data.get("confidence_score", 0.0)),
            issues=all_issues,
            suggestions=data.get("suggestions", []),
        )
        logger.info(
            "[Validator] passed=%s, score=%.2f",
            validation_result.passed,
            validation_result.confidence_score,
        )
    except Exception as exc:
        logger.error("[Validator] Parsing error: %s", exc)
        errors.append(f"[Validator] Parsing error: {exc}")
        validation_result = ValidationResult(
            passed=False,
            confidence_score=0.0,
            issues=[str(exc)],
        )

    # Export to Word if validation passed or score is acceptable
    if validation_result and validation_result.confidence_score >= MIN_CONFIDENCE_SCORE:
        try:
            output_path = generate_word_document(state)
            logger.info("[Validator] Word document generated: %s", output_path)
        except Exception as exc:
            logger.error("[Validator] Word export failed: %s", exc)
            errors.append(f"[Validator] Word export failed: {exc}")

    next_step = AgentStep.END
    if validation_result and not validation_result.passed:
        retry_count = state.get("retry_count", 0) + 1
        if retry_count < state.get("max_retries", 3):
            next_step = AgentStep.SUPERVISOR
        else:
            next_step = AgentStep.END

    return {
        "validation_result": validation_result,
        "output_path": output_path,
        "next_agent": next_step,
        "current_step": AgentStep.VALIDATOR,
        "retry_count": state.get("retry_count", 0) + (1 if next_step != AgentStep.END else 0),
        "errors": errors,
        "agent_logs": state.get("agent_logs", []) + [
            f"Validator: passed={validation_result.passed if validation_result else False}"
        ],
    }
