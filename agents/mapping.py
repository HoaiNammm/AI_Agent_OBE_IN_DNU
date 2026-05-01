"""
Mapping Agent - Ánh xạ CLO → PI → PLO với mức độ IRMA
"""

import json
from typing import Dict, Any, List
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import suggest_irma_for_bloom
# Layer 1: PI/PLO rules truy cập trực tiếp — KHÔNG qua RAG
from utils.kb import build_mapping_kb_context
# Layer 2: prose context — chỉ supplementary, không phải rule lookup
from rag.retriever import retrieve_domain_context
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
    program = state.get("program") or "GENERIC"
    irma_matrix = state.get("irma_matrix")  # Dict[PI_code, level] hoặc None

    logger.info(f"[Mapping] Bắt đầu ánh xạ {len(clo_list)} CLO | program={program}")

    if not clo_list:
        logger.warning("[Mapping] Không có CLO để ánh xạ")
        return {
            "current_step": "mapping_done",
            "warnings": state.get("warnings", []) + ["Mapping: Không có CLO"],
        }

    # ── Layer 1: PI rules — deterministic, trực tiếp từ kb.py ─────────────────
    # KHÔNG qua Qdrant/cosine similarity. Đảm bảo 100% đầy đủ.
    pi_list_text = build_mapping_kb_context(program)

    # ── Layer 2: prose context — supplementary, có thể thiếu ──────────────────
    # Chỉ dùng để bổ sung ngữ cảnh domain-specific, KHÔNG thay thế rules.
    clo_descriptions = [c.get("description", "") for c in clo_list]
    prose_query = f"{course_name} " + " ".join(clo_descriptions[:3])
    prose_ctx = retrieve_domain_context(prose_query, program=program, k=3)
    if prose_ctx:
        pi_list_text = (
            pi_list_text
            + "\n\n=== NGỮ CẢNH DOMAIN BỔ SUNG (TailieuMD — tham khảo, không phải rule) ==="
            + "\n" + prose_ctx
        )

    # Xây dựng prompt (truyền irma_matrix nếu có)
    system_prompt = build_mapping_system_prompt(pi_list_text, irma_matrix=irma_matrix)
    clo_list_text = _format_clo_list(clo_list)
    course_info = _format_course_info(extracted_info, state)
    user_prompt = build_mapping_user_prompt(
        clo_list_text, course_info,
        program=program,
        course_pi_context="",   # kb context already injected in system prompt
    )

    try:
        raw_response = await call_llm_json_async("mapping", system_prompt, user_prompt)
        json_str = extract_json_from_response(raw_response)
        result = json.loads(json_str)

        clo_mappings = result.get("clo_mappings", [])
        mapping_matrix = result.get("mapping_matrix", [])

        # Lọc bỏ PI codes không thuộc chương trình hiện tại
        clo_mappings, mapping_matrix, pi_warnings = _filter_invalid_pi_codes(
            clo_mappings, mapping_matrix, program
        )

        # Cập nhật clo_list với thông tin mapping
        updated_clo_list = _update_clo_with_mapping(clo_list, clo_mappings)

        logger.info(
            f"[Mapping] Hoàn thành: {len(mapping_matrix)} ánh xạ CLO-PI-PLO"
        )

        return {
            "clo_list": updated_clo_list,
            "mapping_matrix": mapping_matrix,
            "current_step": "mapping_done",
            "warnings": state.get("warnings", []) + pi_warnings,
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


def _filter_invalid_pi_codes(
    clo_mappings: List[Dict],
    mapping_matrix: List[Dict],
    program: str,
) -> tuple:
    """
    Lọc bỏ PI codes không thuộc chương trình đào tạo hiện tại.
    Sử dụng kb.get_all_pi_flat() — deterministic, không qua vector search.
    Trả về (clo_mappings, mapping_matrix, warnings).
    """
    from utils.kb import get_all_pi_flat
    valid_pi_codes: set = set(get_all_pi_flat(program).keys())

    if not valid_pi_codes:
        # GENERIC không có PI cụ thể — bỏ qua lọc
        return clo_mappings, mapping_matrix, []

    warnings = []

    # Lọc clo_mappings
    cleaned_mappings = []
    for m in clo_mappings:
        pi_codes   = m.get("pi_codes", [])
        irma_levels = m.get("irma_levels", {})
        invalid = [p for p in pi_codes if p not in valid_pi_codes]
        if invalid:
            warnings.append(
                f"[Mapping] CLO {m.get('clo_code')}: loại bỏ PI không hợp lệ cho {program}: {invalid}"
            )
            for p in invalid:
                logger.warning("[Mapping/Filter] Loại PI không hợp lệ: %s (program=%s)", p, program)
        pi_codes    = [p for p in pi_codes if p in valid_pi_codes]
        irma_levels = {k: v for k, v in irma_levels.items() if k in valid_pi_codes}
        cleaned_mappings.append({**m, "pi_codes": pi_codes, "irma_levels": irma_levels})

    # Lọc mapping_matrix
    cleaned_matrix = []
    for row in mapping_matrix:
        pi_code = row.get("pi_code", "")
        if pi_code and pi_code not in valid_pi_codes:
            warnings.append(
                f"[Mapping] mapping_matrix: loại bỏ hàng với PI không hợp lệ: {pi_code}"
            )
            logger.warning("[Mapping/Filter] Loại hàng PI không hợp lệ: %s", pi_code)
            continue
        cleaned_matrix.append(row)

    return cleaned_mappings, cleaned_matrix, warnings

