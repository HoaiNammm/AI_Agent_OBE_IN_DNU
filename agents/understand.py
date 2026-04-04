"""
Understand Agent - Phân tích học phần và sinh CLO theo Bloom Taxonomy
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import get_bloom_level
from prompts.understand_prompt import (
    UNDERSTAND_SYSTEM_PROMPT,
    build_understand_user_prompt,
)

logger = get_logger("agents.understand")


async def understand_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân tích thông tin học phần và sinh CLO.
    
    Input state: course_code, course_name, credits, summary, outline, human_feedback
    Output state: extracted_info, clo_list, current_step="understand_done"
    """
    course_code = state.get("course_code", "")
    course_name = state.get("course_name", "")
    credits = state.get("credits", "3")
    summary = state.get("summary", "")
    outline = state.get("outline")
    human_feedback = state.get("human_feedback")
    retry_counts = state.get("retry_counts", {})

    logger.info(f"[Understand] Bắt đầu phân tích: {course_code} - {course_name}")

    user_prompt = build_understand_user_prompt(
        course_code=course_code,
        course_name=course_name,
        credits=credits,
        summary=summary,
        outline=outline,
        human_feedback=human_feedback,
    )

    try:
        raw_response = await call_llm_json_async(
            "understand", UNDERSTAND_SYSTEM_PROMPT, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        extracted_info = result.get("extracted_info", {})
        clo_raw_list = result.get("clo_list", [])

        # Normalize CLO list
        clo_list = _normalize_clo_list(clo_raw_list)

        logger.info(
            f"[Understand] Hoàn thành: {len(clo_list)} CLO, "
            f"tín chỉ={extracted_info.get('credits', credits)}"
        )

        return {
            "extracted_info": extracted_info,
            "clo_list": clo_list,
            "current_step": "understand_done",
            "errors": [],
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Understand] Lỗi parse JSON: {e}")
        return {
            "current_step": "understand_done",
            "errors": state.get("errors", []) + [f"Understand: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[Understand] Lỗi: {e}")
        return {
            "current_step": "understand_done",
            "errors": state.get("errors", []) + [f"Understand: {e}"],
        }


def _normalize_clo_list(clo_raw_list: List[Dict]) -> List[Dict]:
    """Chuẩn hóa và validate danh sách CLO."""
    normalized = []

    for i, clo in enumerate(clo_raw_list):
        code = clo.get("code") or f"CLO{i + 1}"
        description = clo.get("description", "").strip()
        bloom_verb = clo.get("bloom_verb", "").strip()

        if not description:
            continue

        # Tự động xác định bloom level nếu thiếu
        bloom_level = clo.get("bloom_level")
        bloom_level_name = clo.get("bloom_level_name", "")
        if not bloom_level and bloom_verb:
            bloom_level, bloom_level_name = get_bloom_level(bloom_verb)

        normalized.append({
            "code": code,
            "description": description,
            "bloom_verb": bloom_verb,
            "bloom_level": bloom_level or 2,
            "bloom_level_name": bloom_level_name or "Hiểu (Understand)",
            "pi_codes": clo.get("pi_codes", []),
            "mapping_level": clo.get("mapping_level", ""),
        })

    return normalized
