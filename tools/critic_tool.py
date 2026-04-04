"""
Critic Tool - Agent phản biện độc lập, kiểm chứng output của từng agent
"""

import json
from typing import Dict, Any
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from prompts.critic_prompt import build_critic_system_prompt, build_critic_user_prompt

logger = get_logger("tools.critic")


async def critic_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Critic Agent kiểm tra output của bước vừa hoàn thành.
    
    Đọc current_step để biết cần review gì:
    - understand_done → review CLO
    - mapping_done → review mapping
    - teaching_plan_done → review teaching plan
    - assessment_done → review assessment
    
    Output: cập nhật critic_feedback list
    """
    current_step = state.get("current_step", "")

    # Map từ done step sang tên bước để review
    step_map = {
        "understand_done": "understand",
        "mapping_done": "mapping",
        "teaching_plan_done": "teaching_plan",
        "assessment_done": "assessment",
    }

    step_name = step_map.get(current_step)
    if not step_name:
        logger.warning(f"[Critic] Không xác định được bước cần review: {current_step}")
        return {}

    logger.info(f"[Critic] Đang review bước: {step_name}")

    # Lấy output cần review
    output_json, context = _extract_step_output(state, step_name)

    system_prompt = build_critic_system_prompt(step_name)
    user_prompt = build_critic_user_prompt(step_name, output_json, context)

    try:
        raw_response = await call_llm_json_async(
            "critic", system_prompt, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        feedback = json.loads(json_str)

        # Đảm bảo có đủ fields
        feedback.setdefault("step", step_name)
        feedback.setdefault("passed", True)
        feedback.setdefault("score", 70)
        feedback.setdefault("critical_issues", [])
        feedback.setdefault("minor_issues", [])
        feedback.setdefault("suggestions", [])
        feedback.setdefault("summary", "")

        passed = feedback.get("passed", True)
        score = feedback.get("score", 70)
        logger.info(
            f"[Critic] {step_name}: {'✓ PASS' if passed else '✗ FAIL'} "
            f"(score={score})"
        )
        if feedback.get("critical_issues"):
            logger.warning(f"[Critic] Critical issues: {feedback['critical_issues']}")

        # Append feedback vào list hiện có
        existing_feedback = list(state.get("critic_feedback", []))
        existing_feedback.append(feedback)

        return {"critic_feedback": existing_feedback}

    except json.JSONDecodeError as e:
        logger.error(f"[Critic] Lỗi parse JSON: {e}")
        # Fallback: pass if no obvious issues
        feedback = _basic_critic(state, step_name)
        existing_feedback = list(state.get("critic_feedback", []))
        existing_feedback.append(feedback)
        return {"critic_feedback": existing_feedback}

    except Exception as e:
        logger.error(f"[Critic] Lỗi: {e}")
        feedback = _basic_critic(state, step_name)
        existing_feedback = list(state.get("critic_feedback", []))
        existing_feedback.append(feedback)
        return {"critic_feedback": existing_feedback}


def _extract_step_output(state: Dict, step_name: str) -> tuple:
    """Trích xuất output và context cho từng bước."""
    if step_name == "understand":
        output = {
            "clo_count": len(state.get("clo_list", [])),
            "clo_list": state.get("clo_list", []),
            "extracted_info": state.get("extracted_info", {}),
        }
        context = f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}"

    elif step_name == "mapping":
        output = {
            "mapping_matrix": state.get("mapping_matrix", []),
            "clo_with_pis": [
                {"code": c["code"], "pi_codes": c.get("pi_codes", []),
                 "mapping_level": c.get("mapping_level", "")}
                for c in state.get("clo_list", [])
            ],
        }
        context = f"{len(state.get('clo_list', []))} CLO cần được ánh xạ"

    elif step_name == "teaching_plan":
        plan = state.get("teaching_plan", [])
        output = {
            "total_sessions": len(plan),
            "teaching_plan_sample": plan[:5],  # chỉ gửi mẫu
            "clo_coverage": _count_clo_coverage(plan),
        }
        context = f"Học phần {state.get('credits', '3')} tín chỉ, {len(state.get('clo_list', []))} CLO"

    elif step_name == "assessment":
        assessment_plan = state.get("assessment_plan", [])
        total_weight = sum(float(a.get("weight", 0)) for a in assessment_plan)
        output = {
            "assessment_plan": assessment_plan,
            "total_weight": round(total_weight, 2),
            "rubrics_available": list(state.get("rubrics", {}).keys()),
        }
        context = f"{len(state.get('clo_list', []))} CLO cần được đánh giá"

    else:
        output = {}
        context = ""

    return json.dumps(output, ensure_ascii=False, indent=2), context


def _count_clo_coverage(teaching_plan) -> Dict:
    """Đếm số buổi mỗi CLO được dạy."""
    coverage = {}
    for session in teaching_plan:
        for clo in session.get("clo_codes", []):
            coverage[clo] = coverage.get(clo, 0) + 1
    return coverage


def _basic_critic(state: Dict, step_name: str) -> Dict:
    """Critic cơ bản không cần LLM (fallback)."""
    issues = []
    passed = True

    if step_name == "understand":
        clo_count = len(state.get("clo_list", []))
        if clo_count < 3:
            issues.append(f"Quá ít CLO: {clo_count}")
            passed = False

    elif step_name == "mapping":
        if not state.get("mapping_matrix"):
            issues.append("Mapping matrix trống")
            passed = False

    elif step_name == "teaching_plan":
        if not state.get("teaching_plan"):
            issues.append("Kế hoạch giảng dạy trống")
            passed = False

    elif step_name == "assessment":
        assessment_plan = state.get("assessment_plan", [])
        if not assessment_plan:
            issues.append("Assessment plan trống")
            passed = False
        else:
            total = sum(float(a.get("weight", 0)) for a in assessment_plan)
            if abs(total - 1.0) > 0.05:
                issues.append(f"Trọng số không hợp lệ: {total:.2f}")
                passed = False

    return {
        "step": step_name,
        "passed": passed,
        "score": 70 if passed else 40,
        "critical_issues": issues if not passed else [],
        "minor_issues": [],
        "suggestions": [],
        "summary": f"Basic validation: {'PASS' if passed else 'FAIL'}",
    }
