"""
Validator Agent - Kiểm chứng tổng thể DCCT và tính confidence score
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import get_program_pi_data
from prompts.validator_prompt import VALIDATOR_SYSTEM_PROMPT, build_validator_user_prompt

logger = get_logger("agents.validator")

PENALTY_PER_BASIC_ISSUE = 5  # điểm trừ cho mỗi vấn đề cơ bản


async def final_validator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Kiểm tra tổng thể DCCT và tính confidence score.
    
    Input state: tất cả thông tin đã xây dựng
    Output state: confidence_score, final_dcct_data, current_step="final_validator_done"
    """
    clo_list = state.get("clo_list", [])
    mapping_matrix = state.get("mapping_matrix", [])
    teaching_plan = state.get("teaching_plan", [])
    assessment_plan = state.get("assessment_plan", [])
    extracted_info = state.get("extracted_info", {})

    logger.info("[Validator] Bắt đầu kiểm chứng tổng thể DCCT")

    # Kiểm tra cơ bản trước khi gọi LLM
    basic_issues = _basic_validation(clo_list, mapping_matrix, teaching_plan, assessment_plan, state)
    if basic_issues:
        logger.warning(f"[Validator] Vấn đề cơ bản: {basic_issues}")

    # Chuẩn bị dữ liệu cho LLM validation
    course_info = (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {state.get('credits', '3')}\n"
        f"Loại: {extracted_info.get('course_type', 'N/A')}"
    )

    clo_json = json.dumps(
        [{"code": c["code"], "description": c["description"],
          "bloom_level": c.get("bloom_level", 2), "pi_codes": c.get("pi_codes", [])}
         for c in clo_list],
        ensure_ascii=False, indent=2
    )

    mapping_json = json.dumps(mapping_matrix[:10], ensure_ascii=False, indent=2)  # giới hạn size

    plan_summary = json.dumps(
        [{"no": s["no"], "content": s["content"], "clo_codes": s["clo_codes"],
          "type": s["type"]}
         for s in teaching_plan[:5]],  # chỉ gửi 5 buổi đầu làm mẫu
        ensure_ascii=False, indent=2
    )

    assessment_json = json.dumps(
        [{"code": a["code"], "name": a["name"], "weight": a["weight"],
          "clo_mapping": a["clo_mapping"]}
         for a in assessment_plan],
        ensure_ascii=False, indent=2
    )

    user_prompt = build_validator_user_prompt(
        course_info, clo_json, mapping_json, plan_summary, assessment_json
    )

    try:
        raw_response = await call_llm_json_async(
            "validator", VALIDATOR_SYSTEM_PROMPT, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        confidence_score = float(result.get("confidence_score", 60.0))
        validation_results = result.get("validation_results", {})
        critical_issues = result.get("critical_issues", [])

        # Trừ điểm cho các vấn đề cơ bản
        if basic_issues:
            confidence_score = max(0, confidence_score - len(basic_issues) * PENALTY_PER_BASIC_ISSUE)

        # Xây dựng final_dcct_data
        final_dcct_data = _build_final_dcct(state, validation_results)

        logger.info(
            f"[Validator] Hoàn thành: confidence={confidence_score:.1f}%, "
            f"status={result.get('overall_status', 'N/A')}"
        )

        return {
            "confidence_score": confidence_score,
            "final_dcct_data": final_dcct_data,
            "warnings": state.get("warnings", []) + critical_issues,
            "current_step": "final_validator",  # Giữ để graph routing hoạt động
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Validator] Lỗi parse JSON: {e}")
        confidence_score = _calculate_basic_confidence(state)
        final_dcct_data = _build_final_dcct(state, {})
        return {
            "confidence_score": confidence_score,
            "final_dcct_data": final_dcct_data,
            "current_step": "final_validator",
            "errors": state.get("errors", []) + [f"Validator: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[Validator] Lỗi: {e}")
        confidence_score = _calculate_basic_confidence(state)
        final_dcct_data = _build_final_dcct(state, {})
        return {
            "confidence_score": confidence_score,
            "final_dcct_data": final_dcct_data,
            "current_step": "final_validator",
            "errors": state.get("errors", []) + [f"Validator: {e}"],
        }


def _basic_validation(
    clo_list, mapping_matrix, teaching_plan, assessment_plan, state: Dict = None
) -> list:
    """Kiểm tra các điều kiện cơ bản không cần LLM."""
    issues = []

    if len(clo_list) < 3:
        issues.append(f"Quá ít CLO: {len(clo_list)} (tối thiểu 3)")

    if not mapping_matrix:
        issues.append("Chưa có mapping matrix")

    if not teaching_plan:
        issues.append("Chưa có kế hoạch giảng dạy")

    if assessment_plan:
        total_weight = sum(float(a.get("weight", 0)) for a in assessment_plan)
        if abs(total_weight - 1.0) > 0.05:
            issues.append(f"Trọng số đánh giá không hợp lệ: {total_weight:.2f} (cần = 1.0)")

    # ── Kiểm tra tính toàn vẹn dữ liệu người dùng ─────────────────────────
    if state:
        program = state.get("program", "GENERIC")
        extracted_info = state.get("extracted_info", {})

        # Kiểm tra credits không bị thay đổi
        user_credits = str(state.get("credits", "")).strip()
        info_credits = str(extracted_info.get("credits", "")).strip()
        if user_credits and info_credits and user_credits != info_credits:
            issues.append(
                f"Số tín chỉ trong extracted_info ({info_credits}) khác với đầu vào ({user_credits})"
            )

        # Kiểm tra course_code không bị thay đổi
        user_code = str(state.get("course_code", "")).strip()
        info_code = str(extracted_info.get("course_code", "")).strip()
        if user_code and info_code and user_code.upper() != info_code.upper():
            issues.append(
                f"Mã học phần trong extracted_info ({info_code}) khác với đầu vào ({user_code})"
            )

        # Kiểm tra PI codes thuộc đúng chương trình (chỉ khi không phải GENERIC)
        if program != "GENERIC" and mapping_matrix:
            pi_data = get_program_pi_data(program)
            valid_pi_codes: set = set()
            for pis in pi_data.values():
                valid_pi_codes.update(pis.keys())

            invalid_pis: List[str] = []
            for row in mapping_matrix:
                pi_code = row.get("pi_code", "")
                if pi_code and pi_code not in valid_pi_codes:
                    invalid_pis.append(pi_code)

            if invalid_pis:
                issues.append(
                    f"PI codes không thuộc chương trình {program}: {list(set(invalid_pis))}"
                )

    return issues


def _calculate_basic_confidence(state: Dict) -> float:
    """Tính confidence cơ bản không cần LLM."""
    score = 0

    clo_list = state.get("clo_list", [])
    mapping_matrix = state.get("mapping_matrix", [])
    teaching_plan = state.get("teaching_plan", [])
    assessment_plan = state.get("assessment_plan", [])

    if 4 <= len(clo_list) <= 9:
        score += 20
    elif len(clo_list) >= 3:
        score += 10

    if mapping_matrix:
        score += 20

    if len(teaching_plan) >= 10:
        score += 20

    if len(assessment_plan) >= 3:
        total_weight = sum(float(a.get("weight", 0)) for a in assessment_plan)
        if abs(total_weight - 1.0) < 0.05:
            score += 20

    if not state.get("errors"):
        score += 10

    return min(score, 80.0)


def _build_final_dcct(state: Dict, validation_results: Dict) -> Dict:
    """Tổng hợp toàn bộ dữ liệu DCCT."""
    return {
        "course_info": {
            "code": state.get("course_code", ""),
            "name": state.get("course_name", ""),
            "credits": state.get("credits", "3"),
            **state.get("extracted_info", {}),
        },
        "clo_list": state.get("clo_list", []),
        "mapping_matrix": state.get("mapping_matrix", []),
        "teaching_plan": state.get("teaching_plan", []),
        "assessment_plan": state.get("assessment_plan", []),
        "rubrics": state.get("rubrics", {}),
        "validation": validation_results,
        "confidence_score": state.get("confidence_score", 0),
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
    }
