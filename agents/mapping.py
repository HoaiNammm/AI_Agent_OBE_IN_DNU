"""
Mapping Agent - Ánh xạ CLO → PI → PLO với mức độ IRMA
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import get_pi_list_text, get_plo_for_pi, suggest_irma_for_bloom
from rag.retriever import get_plo_pi_context_for_course
from prompts.mapping_prompt import build_mapping_system_prompt, build_mapping_user_prompt

logger = get_logger("agents.mapping")


async def mapping_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ánh xạ CLO → PI → PLO với mức IRMA.
    
    Input state: clo_list, extracted_info
    Output state: clo_list (updated with pi_codes, mapping_level), mapping_matrix
    """
    clo_list = state.get("clo_list", [])
    extracted_info = state.get("extracted_info", {})
    course_name = state.get("course_name", "")

    logger.info(f"[Mapping] Bắt đầu ánh xạ {len(clo_list)} CLO")

    if not clo_list:
        logger.warning("[Mapping] Không có CLO để ánh xạ")
        return {
            "current_step": "mapping_done",
            "warnings": state.get("warnings", []) + ["Mapping: Không có CLO"],
        }

    # Xây dựng context PLO/PI từ RAG
    clo_descriptions = [c.get("description", "") for c in clo_list]
    obe_context = get_plo_pi_context_for_course(course_name, clo_descriptions)

    # Xây dựng prompt
    system_prompt = build_mapping_system_prompt(get_pi_list_text())
    clo_list_text = _format_clo_list(clo_list)
    course_info = _format_course_info(extracted_info, state)
    user_prompt = build_mapping_user_prompt(clo_list_text, course_info)

    try:
        raw_response = await call_llm_json_async("mapping", system_prompt, user_prompt)
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        clo_mappings = result.get("clo_mappings", [])
        mapping_matrix = result.get("mapping_matrix", [])

        # Cập nhật clo_list với thông tin mapping
        updated_clo_list = _update_clo_with_mapping(clo_list, clo_mappings)

        logger.info(
            f"[Mapping] Hoàn thành: {len(mapping_matrix)} ánh xạ CLO-PI-PLO"
        )

        return {
            "clo_list": updated_clo_list,
            "mapping_matrix": mapping_matrix,
            "current_step": "mapping_done",
        }

    except json.JSONDecodeError as e:
        logger.error(f"[Mapping] Lỗi parse JSON: {e}")
        # Fallback: tự sinh mapping cơ bản
        fallback_matrix = _generate_fallback_mapping(clo_list)
        return {
            "clo_list": clo_list,
            "mapping_matrix": fallback_matrix,
            "current_step": "mapping_done",
            "errors": state.get("errors", []) + [f"Mapping: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[Mapping] Lỗi: {e}")
        fallback_matrix = _generate_fallback_mapping(clo_list)
        return {
            "clo_list": clo_list,
            "mapping_matrix": fallback_matrix,
            "current_step": "mapping_done",
            "errors": state.get("errors", []) + [f"Mapping: {e}"],
        }


def _format_clo_list(clo_list: List[Dict]) -> str:
    lines = []
    for clo in clo_list:
        lines.append(
            f"{clo['code']} [Bloom {clo.get('bloom_level', 2)} - {clo.get('bloom_level_name', '')}]: "
            f"{clo['description']}"
        )
    return "\n".join(lines)


def _format_course_info(extracted_info: Dict, state: Dict) -> str:
    return (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {extracted_info.get('credits', state.get('credits', '3'))}\n"
        f"Lĩnh vực: {', '.join(extracted_info.get('knowledge_areas', []))}"
    )


def _update_clo_with_mapping(
    clo_list: List[Dict], clo_mappings: List[Dict]
) -> List[Dict]:
    """Cập nhật clo_list với thông tin pi_codes và mapping_level."""
    mapping_by_code = {m["clo_code"]: m for m in clo_mappings}

    updated = []
    for clo in clo_list:
        mapping = mapping_by_code.get(clo["code"], {})
        irma_levels = mapping.get("irma_levels", {})
        pi_codes = mapping.get("pi_codes", [])

        # Lấy mức IRMA chính (của PI đầu tiên hoặc gợi ý từ Bloom)
        primary_irma = ""
        if irma_levels and pi_codes:
            primary_irma = irma_levels.get(pi_codes[0], "")
        if not primary_irma:
            bloom_level = clo.get("bloom_level", 2)
            primary_irma = suggest_irma_for_bloom(bloom_level)

        updated.append({
            **clo,
            "pi_codes": pi_codes,
            "mapping_level": primary_irma,
        })

    return updated


def _generate_fallback_mapping(clo_list: List[Dict]) -> List[Dict]:
    """Tự sinh mapping cơ bản khi LLM fail."""
    from utils.obe_utils import PI_DATA

    # PLO mặc định cho IT course
    default_plos = ["PLO1", "PLO3", "PLO4"]
    matrix = []

    for i, clo in enumerate(clo_list):
        bloom_level = clo.get("bloom_level", 2)
        irma = suggest_irma_for_bloom(bloom_level)
        plo = default_plos[i % len(default_plos)]
        pis = list(PI_DATA.get(plo, {}).keys())
        pi = pis[0] if pis else "PI1.1"

        matrix.append({
            "clo_code": clo["code"],
            "plo_code": plo,
            "pi_code": pi,
            "irma_level": irma,
            "bloom_level": bloom_level,
        })

    return matrix
