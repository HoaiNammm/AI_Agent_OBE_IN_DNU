"""
Assessment Agent - Thiết kế hệ thống đánh giá A1/A2.1/A2.2/A3 và Rubric
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import DEFAULT_ASSESSMENT_WEIGHTS
from prompts.assessment_prompt import (
    ASSESSMENT_SYSTEM_PROMPT,
    build_assessment_user_prompt,
)

logger = get_logger("agents.assessment")


async def assessment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Thiết kế hệ thống đánh giá và rubric.
    
    Input state: clo_list, mapping_matrix, teaching_plan, extracted_info
    Output state: assessment_plan, rubrics, current_step="assessment_done"
    """
    clo_list = state.get("clo_list", [])
    mapping_matrix = state.get("mapping_matrix", [])
    extracted_info = state.get("extracted_info", {})

    logger.info(f"[Assessment] Thiết kế đánh giá cho {len(clo_list)} CLO")

    if not clo_list:
        logger.warning("[Assessment] Không có CLO — bỏ qua sinh đánh giá")
        return {
            "assessment_plan": [],
            "rubrics": {},
            "current_step": "assessment_done",
            "warnings": state.get("warnings", []) + [
                "Hệ thống đánh giá trống vì không có CLO. Vui lòng kiểm tra lại đề cương đầu vào."
            ],
        }

    has_lab = int(extracted_info.get("lab_periods", 0) or 0) > 0
    clo_list_text = _format_clo_list(clo_list)
    mapping_summary = _format_mapping_summary(mapping_matrix, clo_list)
    course_info = (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {state.get('credits', '3')}\n"
        f"Loại: {extracted_info.get('course_type', 'lý thuyết+thực hành')}"
    )

    user_prompt = build_assessment_user_prompt(
        course_info, clo_list_text, mapping_summary, has_lab
    )

    try:
        raw_response = await call_llm_json_async(
            "assessment", ASSESSMENT_SYSTEM_PROMPT, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        assessment_plan = result.get("assessment_plan", [])
        rubrics = result.get("rubrics", {})
        grading_policy = result.get("grading_policy", {})

        assessment_plan = _normalize_assessment_plan(assessment_plan, clo_list)

        # Gắn truy_vet (Assessment-CLO-PI-PLO) vào rubrics để export
        if grading_policy:
            rubrics["traceability"] = grading_policy

        logger.info(
            f"[Assessment] Hoàn thành: {len(assessment_plan)} cấu phần đánh giá"
        )

        return {
            "assessment_plan": assessment_plan,
            "rubrics": rubrics,
            "current_step": "assessment_done",
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Assessment] Lỗi parse JSON: {e}")
        fallback_plan = _generate_fallback_assessment(clo_list)
        return {
            "assessment_plan": fallback_plan["assessment_plan"],
            "rubrics": fallback_plan["rubrics"],
            "current_step": "assessment_done",
            "errors": state.get("errors", []) + [f"Assessment: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[Assessment] Lỗi: {e}")
        fallback_plan = _generate_fallback_assessment(clo_list)
        return {
            "assessment_plan": fallback_plan["assessment_plan"],
            "rubrics": fallback_plan["rubrics"],
            "current_step": "assessment_done",
            "errors": state.get("errors", []) + [f"Assessment: {e}"],
        }


def _format_clo_list(clo_list: List[Dict]) -> str:
    lines = []
    for clo in clo_list:
        lines.append(
            f"{clo['code']} [Bloom {clo.get('bloom_level', 2)} - "
            f"IRMA: {clo.get('mapping_level', 'R')}]: {clo['description']}"
        )
    return "\n".join(lines)


def _format_mapping_summary(mapping_matrix: List[Dict], clo_list: List[Dict]) -> str:
    if not mapping_matrix:
        return "Chưa có mapping"
    lines = []
    for clo in clo_list:
        mappings = [m for m in mapping_matrix if m.get("clo_code") == clo["code"]]
        plos = list({m.get("plo_code", "") for m in mappings})
        lines.append(f"{clo['code']} → {', '.join(plos)}")
    return "\n".join(lines)


def _normalize_assessment_plan(plan: List[Dict], clo_list: List[Dict]) -> List[Dict]:
    """Chuẩn hóa assessment plan, đảm bảo trọng số = 100%."""
    if not plan:
        return _generate_fallback_assessment(clo_list)["assessment_plan"]

    # Đảm bảo trọng số cộng thành 1.0
    total_weight = sum(float(p.get("weight", 0)) for p in plan)
    if abs(total_weight - 1.0) > 0.01 and total_weight > 0:
        for p in plan:
            p["weight"] = round(float(p.get("weight", 0)) / total_weight, 2)

    normalized = []
    for p in plan:
        normalized.append({
            "code": p.get("code", "A1"),
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "weight": float(p.get("weight", 0.1)),
            "format": p.get("format", ""),
            "timing": p.get("timing", p.get("frequency", "")),
            "frequency": p.get("frequency", ""),
            "criteria_summary": p.get("criteria_summary", ""),
            "clo_mapping": p.get("clo_mapping", []),
            "pi_codes": p.get("pi_codes", []),
            "plo_codes": p.get("plo_codes", []),
            "truy_vet_note": p.get("truy_vet_note", ""),
            "bloom_levels_assessed": p.get("bloom_levels_assessed", []),
            "duration_minutes": p.get("duration_minutes"),
        })

    return normalized


def _generate_fallback_assessment(clo_list: List[Dict]) -> Dict:
    """
    Fallback assessment khi LLM thất bại.
    Sinh rubric dựa trên CLO thực tế của học phần — không hardcode criteria generic.
    """
    clo_codes = [c["code"] for c in clo_list]
    mid = max(1, len(clo_codes) // 2)
    a21_clos = clo_codes[:mid]
    a22_clos = clo_codes[mid:]

    assessment_plan = [
        {
            **DEFAULT_ASSESSMENT_WEIGHTS["A1"],
            "code": "A1",
            "timing": "Mỗi buổi học",
            "clo_mapping": [],
            "pi_codes": [],
            "plo_codes": [],
            "truy_vet_note": "Dùng cho điểm quá trình; không dùng đơn lẻ để kết luận CLO/PLO.",
            "bloom_levels_assessed": [],
            "duration_minutes": None,
        },
        {
            **DEFAULT_ASSESSMENT_WEIGHTS["A2.1"],
            "code": "A2.1",
            "timing": "Sau chủ đề 1–3",
            "clo_mapping": a21_clos,
            "pi_codes": [],
            "plo_codes": [],
            "truy_vet_note": "[CÓ CĂN CỨ] Đo lường CLO giai đoạn đầu học phần.",
            "bloom_levels_assessed": [1, 2, 3],
            "duration_minutes": None,
        },
        {
            **DEFAULT_ASSESSMENT_WEIGHTS["A2.2"],
            "code": "A2.2",
            "timing": "Sau chủ đề 4–7",
            "clo_mapping": a22_clos,
            "pi_codes": [],
            "plo_codes": [],
            "truy_vet_note": "[CÓ CĂN CỨ] Đo lường CLO giai đoạn giữa-cuối học phần.",
            "bloom_levels_assessed": [3, 4, 5],
            "duration_minutes": None,
        },
        {
            **DEFAULT_ASSESSMENT_WEIGHTS["A3"],
            "code": "A3",
            "timing": "Theo lịch nhà trường",
            "clo_mapping": clo_codes,
            "pi_codes": [],
            "plo_codes": [],
            "truy_vet_note": "[CÓ CĂN CỨ] Bằng chứng tổng hợp, đo lường toàn bộ CLO.",
            "bloom_levels_assessed": [1, 2, 3, 4, 5, 6],
            "duration_minutes": None,
        },
    ]

    rubrics = _build_clo_based_rubric(clo_list, a21_clos, a22_clos)
    return {"assessment_plan": assessment_plan, "rubrics": rubrics}


def _build_clo_based_rubric(
    clo_list: List[Dict],
    a21_clos: List[str],
    a22_clos: List[str],
) -> Dict:
    """
    Xây dựng rubric fallback trực tiếp từ mô tả CLO của học phần.
    Mỗi CLO → 1 criterion gắn đúng với cấu phần đánh giá nó.
    """
    a1_criteria = [
        {
            "criterion": "Tham dự và tham gia lớp học",
            "clo_measured": "Không dùng để kết luận CLO",
            "weight_in_component": 0.30,
            "levels": {
                "M1": "Vắng nhiều buổi hoặc thường xuyên đi muộn",
                "M2": "Tham dự không ổn định; còn đi muộn hoặc bỏ tiết",
                "M3": "Tham dự đạt mức tối thiểu theo quy định",
                "M4": "Tham dự đầy đủ, đúng giờ trong hầu hết các buổi",
                "M5": "Tham dự đầy đủ, đúng giờ, chủ động hỗ trợ hoạt động lớp",
            },
        },
        {
            "criterion": "Chuẩn bị trước giờ học",
            "clo_measured": "Không dùng để kết luận CLO",
            "weight_in_component": 0.20,
            "levels": {
                "M1": "Không chuẩn bị học liệu hoặc yêu cầu trước giờ học",
                "M2": "Có chuẩn bị nhưng rời rạc, chưa đáp ứng yêu cầu chính",
                "M3": "Chuẩn bị được học liệu và yêu cầu tối thiểu",
                "M4": "Chuẩn bị tương đối đầy đủ, bám yêu cầu buổi học",
                "M5": "Chuẩn bị đầy đủ, có ghi chú hoặc câu hỏi kỹ thuật phù hợp",
            },
        },
        {
            "criterion": "Tham gia thảo luận và thực hành",
            "clo_measured": "Không dùng để kết luận CLO",
            "weight_in_component": 0.30,
            "levels": {
                "M1": "Không tham gia hoặc từ chối thực hành/thảo luận",
                "M2": "Tham gia hạn chế, chủ yếu làm theo mà không có đóng góp",
                "M3": "Tham gia ở mức tối thiểu, hoàn thành yêu cầu cơ bản",
                "M4": "Tham gia chủ động, thực hiện tốt hoạt động thảo luận/thực hành",
                "M5": "Tham gia tích cực, có trao đổi học thuật hoặc hỗ trợ nhóm/lớp hiệu quả",
            },
        },
        {
            "criterion": "Tuân thủ quy định và thái độ học tập",
            "clo_measured": "Không dùng để kết luận CLO",
            "weight_in_component": 0.20,
            "levels": {
                "M1": "Vi phạm quy định lớp học hoặc thể hiện thái độ thiếu hợp tác",
                "M2": "Còn nhắc nhở về tác phong hoặc nộp/báo cáo nhiệm vụ chậm",
                "M3": "Tuân thủ quy định cơ bản, thái độ học tập phù hợp",
                "M4": "Tuân thủ tốt, hợp tác tốt với giảng viên và bạn học",
                "M5": "Tác phong chuyên nghiệp, hợp tác tốt, góp phần duy trì môi trường học tập tích cực",
            },
        },
    ]

    evidence_criterion = {
        "criterion": "Báo cáo và bộ minh chứng",
        "clo_measured": "Hỗ trợ evidence",
        "weight_in_component": 0.20,
        "levels": {
            "M1": "Thiếu phần lớn minh chứng; báo cáo không đủ để đối chiếu kết quả",
            "M2": "Có minh chứng tối thiểu nhưng rời rạc, khó tái kiểm tra",
            "M3": "Có báo cáo và code/log cơ bản; đối chiếu được các bước chính",
            "M4": "Báo cáo rõ, minh chứng tương đối đủ, trả lời được phản biện cơ bản",
            "M5": "Bộ minh chứng đầy đủ, nhất quán, tái kiểm tra được; báo cáo thuyết phục",
        },
    }

    def _make_clo_criteria(selected_clo_codes: List[str]) -> List[Dict]:
        selected = [c for c in clo_list if c.get("code", "") in selected_clo_codes]
        if not selected:
            selected = clo_list
        n = len(selected)
        clo_weight = round((1.0 - 0.20) / n, 2)  # 20% dành cho evidence
        criteria = []
        for clo in selected:
            desc = clo.get("description", "")
            code = clo.get("code", "CLO")
            short = desc.split(",")[0].split(";")[0].strip()[:80]
            criteria.append({
                "criterion": short,
                "clo_measured": code,
                "weight_in_component": clo_weight,
                "levels": {
                    "M1": f"Không thực hiện được: {short[:50]}",
                    "M2": f"Thực hiện được một phần yêu cầu {code}, còn nhiều hạn chế",
                    "M3": f"Đáp ứng yêu cầu tối thiểu của {code}",
                    "M4": f"Đáp ứng tốt yêu cầu {code}, có căn cứ rõ ràng",
                    "M5": f"Vượt yêu cầu {code}, thể hiện năng lực vững chắc và độc lập",
                },
            })
        return criteria

    return {
        "A1":  {"criteria": a1_criteria},
        "A2.1": {"criteria": _make_clo_criteria(a21_clos) + [evidence_criterion]},
        "A2.2": {"criteria": _make_clo_criteria(a22_clos) + [evidence_criterion]},
        "A3":  {"criteria": _make_clo_criteria([c["code"] for c in clo_list]) + [evidence_criterion]},
    }