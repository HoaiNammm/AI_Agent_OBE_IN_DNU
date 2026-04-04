"""
Teaching Plan Agent - Xây dựng kế hoạch giảng dạy động
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import calculate_sessions
from prompts.teaching_plan_prompt import (
    build_teaching_plan_system_prompt,
    build_teaching_plan_user_prompt,
)

logger = get_logger("agents.teaching_plan")


async def teaching_plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xây dựng kế hoạch giảng dạy chi tiết từng buổi.
    
    Input state: clo_list, mapping_matrix, credits, extracted_info
    Output state: teaching_plan, current_step="teaching_plan_done"
    """
    clo_list = state.get("clo_list", [])
    mapping_matrix = state.get("mapping_matrix", [])
    credits = state.get("credits", "3")
    extracted_info = state.get("extracted_info", {})

    logger.info(f"[TeachingPlan] Xây dựng kế hoạch cho {credits} tín chỉ")

    # Tính phân bổ thời gian
    lab_periods = extracted_info.get("lab_periods", 0)
    theory_periods = extracted_info.get("theory_periods", 0)
    total_theory = int(credits) * 15 if not theory_periods else theory_periods

    has_lab = lab_periods > 0
    theory_ratio = theory_periods / (theory_periods + lab_periods) if (theory_periods + lab_periods) > 0 else 0.7

    session_info = calculate_sessions(credits, theory_ratio)

    # Build prompts
    system_prompt = build_teaching_plan_system_prompt(session_info)
    clo_list_text = _format_clo_list(clo_list)
    mapping_summary = _format_mapping_summary(mapping_matrix)
    course_info = _format_course_info(state, extracted_info, session_info)

    user_prompt = build_teaching_plan_user_prompt(
        course_info, clo_list_text, mapping_summary
    )

    try:
        raw_response = await call_llm_json_async(
            "teaching_plan", system_prompt, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        teaching_plan = result.get("teaching_plan", [])
        teaching_plan = _normalize_plan(teaching_plan)

        logger.info(f"[TeachingPlan] Hoàn thành: {len(teaching_plan)} buổi học")

        return {
            "teaching_plan": teaching_plan,
            "current_step": "teaching_plan_done",
        }

    except json.JSONDecodeError as e:
        logger.error(f"[TeachingPlan] Lỗi parse JSON: {e}")
        fallback_plan = _generate_fallback_plan(clo_list, session_info)
        return {
            "teaching_plan": fallback_plan,
            "current_step": "teaching_plan_done",
            "errors": state.get("errors", []) + [f"TeachingPlan: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[TeachingPlan] Lỗi: {e}")
        fallback_plan = _generate_fallback_plan(clo_list, session_info)
        return {
            "teaching_plan": fallback_plan,
            "current_step": "teaching_plan_done",
            "errors": state.get("errors", []) + [f"TeachingPlan: {e}"],
        }


def _format_clo_list(clo_list: List[Dict]) -> str:
    lines = []
    for clo in clo_list:
        pi_str = ", ".join(clo.get("pi_codes", [])) or "N/A"
        lines.append(
            f"{clo['code']} (IRMA: {clo.get('mapping_level', 'R')}, "
            f"Bloom: {clo.get('bloom_level', 2)}): {clo['description']}\n"
            f"  → PI: {pi_str}"
        )
    return "\n".join(lines)


def _format_mapping_summary(mapping_matrix: List[Dict]) -> str:
    if not mapping_matrix:
        return "Chưa có mapping"
    summary = {}
    for m in mapping_matrix:
        clo = m.get("clo_code", "")
        plo = m.get("plo_code", "")
        if clo not in summary:
            summary[clo] = []
        if plo not in summary[clo]:
            summary[clo].append(plo)
    return "\n".join([f"{clo} → {', '.join(plos)}" for clo, plos in summary.items()])


def _format_course_info(state: Dict, extracted_info: Dict, session_info: Dict) -> str:
    return (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {session_info['credits']}\n"
        f"Tổng tiết: {session_info['total_periods']} (LT: {session_info['theory_periods']}, TH: {session_info['lab_periods']})"
    )


def _normalize_plan(plan: List[Dict]) -> List[Dict]:
    """Chuẩn hóa kế hoạch giảng dạy."""
    normalized = []
    for i, session in enumerate(plan):
        normalized.append({
            "no": session.get("no", i + 1),
            "week": session.get("week", (i // 3) + 1),
            "type": session.get("type", "LT"),
            "content": session.get("content", f"Buổi {i + 1}"),
            "details": session.get("details", ""),
            "clo_codes": session.get("clo_codes", []),
            "irma_level": session.get("irma_level", "R"),
            "activities": session.get("activities", "Lecture"),
            "assessment": session.get("assessment", ""),
            "duration_periods": session.get("duration_periods", 1),
        })
    return normalized


def _generate_fallback_plan(clo_list: List[Dict], session_info: Dict) -> List[Dict]:
    """Tự sinh kế hoạch cơ bản khi LLM fail."""
    plan = []
    total = session_info.get("total_periods", 45)
    theory = session_info.get("theory_periods", 30)
    lab = session_info.get("lab_periods", 15)

    clo_codes = [c["code"] for c in clo_list]
    per_clo = max(1, theory // max(len(clo_codes), 1))

    session_no = 1
    # Buổi đầu: Giới thiệu
    plan.append({
        "no": session_no, "week": 1, "type": "LT",
        "content": "Giới thiệu học phần, tổng quan nội dung",
        "details": "Giới thiệu mục tiêu, yêu cầu và kế hoạch học phần",
        "clo_codes": clo_codes[:2] if clo_codes else [],
        "irma_level": "I", "activities": "Lecture",
        "assessment": "", "duration_periods": 1,
    })
    session_no += 1

    # Các buổi theo CLO
    for i, clo in enumerate(clo_list):
        for j in range(per_clo):
            week = (session_no - 1) // 3 + 1
            plan.append({
                "no": session_no, "week": week, "type": "LT",
                "content": f"Nội dung {clo['code']}: {clo['description'][:60]}...",
                "details": clo["description"],
                "clo_codes": [clo["code"]],
                "irma_level": clo.get("mapping_level", "R"),
                "activities": "Lecture",
                "assessment": "",
                "duration_periods": 1,
            })
            session_no += 1

    # Buổi TH nếu có
    for i in range(min(lab, len(clo_list))):
        clo = clo_list[i % len(clo_list)]
        week = (session_no - 1) // 3 + 1
        plan.append({
            "no": session_no, "week": week, "type": "TH",
            "content": f"Thực hành: {clo['code']}",
            "details": f"Bài tập thực hành liên quan đến {clo['description'][:60]}",
            "clo_codes": [clo["code"]],
            "irma_level": "M",
            "activities": "Lab",
            "assessment": "Chấm bài TH",
            "duration_periods": 1,
        })
        session_no += 1

    # Buổi cuối: Ôn tập
    plan.append({
        "no": session_no, "week": (session_no - 1) // 3 + 1, "type": "LT",
        "content": "Ôn tập tổng hợp và giải đáp thắc mắc",
        "details": "Ôn tập toàn bộ nội dung, hướng dẫn ôn thi",
        "clo_codes": clo_codes,
        "irma_level": "A", "activities": "Review",
        "assessment": "", "duration_periods": 1,
    })

    return plan[:total]
