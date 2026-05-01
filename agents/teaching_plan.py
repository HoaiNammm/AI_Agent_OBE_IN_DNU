"""
Teaching Plan Agent - Xây dựng kế hoạch giảng dạy động.

Hai chế độ:
  PRESERVE (outline_provided=True):
      Dùng outline_sessions làm skeleton bất biến.
      LLM chỉ enrich (CLO, IRMA, hoạt động, đánh giá).
  GENERATE (outline_provided=False):
      LLM tự sinh lịch từ CLO list theo phân bổ tín chỉ.
"""

import json
from typing import Dict, Any, List, Tuple
from utils.logger import get_logger
from utils.llm_helper import call_llm_json_async, extract_json_from_response
from utils.obe_utils import calculate_sessions
from utils.outline_parser import is_raw_text_fallback
from prompts.teaching_plan_prompt import (
    build_teaching_plan_system_prompt,
    build_teaching_plan_user_prompt,
)

logger = get_logger("agents.teaching_plan")


async def teaching_plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xây dựng kế hoạch giảng dạy chi tiết từng buổi.

    Input state:
        clo_list, mapping_matrix, credits, extracted_info,
        outline_provided, outline_sessions, session_clo_map
    Output state:
        teaching_plan, current_step="teaching_plan_done"
    """
    clo_list         = state.get("clo_list", [])
    mapping_matrix   = state.get("mapping_matrix", [])
    credits          = state.get("credits", "3")
    outline_provided = state.get("outline_provided", False)
    outline_sessions = state.get("outline_sessions") or []
    session_clo_map  = state.get("session_clo_map") or {}

    logger.info(
        f"[TeachingPlan] Chế độ={'PRESERVE' if outline_provided else 'GENERATE'} | "
        f"outline_sessions={len(outline_sessions)} | credits={credits}"
    )

    # Cấu trúc buổi học từ state (mặc định 5 tiết/buổi, 3 LT + 2 TH)
    periods_per_session = int(state.get("periods_per_session") or 5)
    theory_per_session  = int(state.get("theory_per_session")  or 3)

    # Nếu PRESERVE: ưu tiên tổng tiết từ outline (tổng estimated_periods)
    if outline_provided and outline_sessions and not is_raw_text_fallback(outline_sessions):
        outline_total = sum(int(s.get("estimated_periods", 1) or 1) for s in outline_sessions)
        if outline_total > 0 and abs(outline_total - int(credits) * 15) > 5:
            logger.info(
                "[TeachingPlan] Tổng tiết outline (%d) khác tổng tín chỉ (%d) — dùng outline làm chuẩn",
                outline_total, int(credits) * 15,
            )

    # ── Dynamic LT/TH split dựa trên phân tích CLO + IRMA ─────────────────
    computed_tps, computed_lps, split_rationale = _compute_session_split(
        clo_list, mapping_matrix, periods_per_session, theory_per_session
    )
    session_info = calculate_sessions(
        credits,
        periods_per_session=periods_per_session,
        theory_per_session=computed_tps,
    )
    logger.info(
        "[TeachingPlan] Split %dLT+%dTH/buổi | %s",
        computed_tps, computed_lps, split_rationale,
    )

    # Build prompts
    system_prompt   = build_teaching_plan_system_prompt(session_info, outline_provided)
    clo_list_text   = _format_clo_list(clo_list)
    mapping_detail  = _format_mapping_detail(mapping_matrix, clo_list)
    mapping_summary = _format_mapping_summary(mapping_matrix)
    course_info     = _format_course_info(state, session_info, split_rationale)

    user_prompt = build_teaching_plan_user_prompt(
        course_info      = course_info,
        clo_list_text    = clo_list_text,
        mapping_summary  = mapping_summary,
        mapping_detail   = mapping_detail,
        outline_sessions = outline_sessions,
        session_clo_map  = session_clo_map,
        outline_provided = outline_provided,
    )

    try:
        raw_response = await call_llm_json_async(
            "teaching_plan", system_prompt, user_prompt
        )
        json_str = extract_json_from_response(raw_response)
        result   = json.loads(json_str)

        teaching_plan = result.get("teaching_plan", [])
        teaching_plan = _normalize_plan(teaching_plan)

        # Guard PRESERVE: kiểm tra số buổi khớp với outline
        if outline_provided and outline_sessions and not is_raw_text_fallback(outline_sessions):
            teaching_plan = _enforce_outline_skeleton(
                teaching_plan, outline_sessions, session_clo_map, clo_list
            )

        logger.info(
            f"[TeachingPlan] Hoàn thành: {len(teaching_plan)} buổi | "
            f"outline_preserved={outline_provided}"
        )

        return {
            "teaching_plan": teaching_plan,
            "current_step":  "teaching_plan_done",
        }

    except json.JSONDecodeError as e:
        logger.error(f"[TeachingPlan] Lỗi parse JSON: {e}")
        fallback = _generate_fallback_plan(
            clo_list, session_info, outline_sessions, session_clo_map, outline_provided
        )
        return {
            "teaching_plan": fallback,
            "current_step":  "teaching_plan_done",
            "errors": state.get("errors", []) + [f"TeachingPlan: Lỗi parse JSON - {e}"],
        }
    except Exception as e:
        logger.error(f"[TeachingPlan] Lỗi: {e}")
        fallback = _generate_fallback_plan(
            clo_list, session_info, outline_sessions, session_clo_map, outline_provided
        )
        return {
            "teaching_plan": fallback,
            "current_step":  "teaching_plan_done",
            "errors": state.get("errors", []) + [f"TeachingPlan: {e}"],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Guard: Preserve outline skeleton
# ─────────────────────────────────────────────────────────────────────────────

def _enforce_outline_skeleton(
    llm_plan: List[Dict],
    outline_sessions: List[Dict],
    session_clo_map: Dict[str, List[str]],
    clo_list: List[Dict],
) -> List[Dict]:
    """
    Đảm bảo teaching_plan khớp với outline GV.
    Nếu LLM thêm/bớt/đổi thứ tự buổi → reset về skeleton outline, giữ enrich từ LLM nếu có.
    """
    outline_count = len(outline_sessions)
    llm_count     = len(llm_plan)

    if llm_count != outline_count:
        logger.warning(
            f"[TeachingPlan/Guard] LLM tạo {llm_count} buổi, outline có {outline_count} buổi — "
            f"áp dụng outline skeleton."
        )

    # Build lookup LLM plan theo no
    llm_by_no = {s.get("no", i + 1): s for i, s in enumerate(llm_plan)}

    corrected = []
    cumulative_periods = 0
    for os_item in outline_sessions:
        no     = os_item["no"]
        topic  = os_item["topic"]
        periods = int(os_item.get("estimated_periods", 1) or 1)
        stype  = os_item.get("session_type", "LT")
        subs   = os_item.get("subtopics", [])

        # Lấy enrich từ LLM nếu có (match theo no)
        llm_s = llm_by_no.get(no, {})

        # week tính theo tích lũy tiết (3 tiết/tuần)
        week = max(1, (cumulative_periods // 3) + 1)
        cumulative_periods += periods

        # CLO từ session_clo_map (ưu tiên); fallback lấy từ LLM
        clos = session_clo_map.get(str(no)) or llm_s.get("clo_codes", [])
        if not clos and clo_list:
            clos = [clo_list[no % len(clo_list)]["code"]]

        corrected.append({
            "no":               no,
            "week":             llm_s.get("week", week),
            "type":             stype,
            "content":          topic,                          # NGUYÊN VĂN GV
            "details":          llm_s.get("details") or ("; ".join(subs) if subs else ""),
            "clo_codes":        clos,
            "irma_level":       llm_s.get("irma_level", "R"),
            "activities":       llm_s.get("activities", "Lecture" if stype == "LT" else "Lab"),
            "assessment":       llm_s.get("assessment", ""),
            "duration_periods": periods,
        })

    return corrected


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_clo_list(clo_list: List[Dict]) -> str:
    lines = []
    for clo in clo_list:
        pi_str = ", ".join(clo.get("pi_codes", [])) or "N/A"
        src    = clo.get("source_sessions", [])
        src_str = f" [từ buổi: {src}]" if src else ""
        lines.append(
            f"{clo['code']} (IRMA: {clo.get('mapping_level', 'R')}, "
            f"Bloom: {clo.get('bloom_level', 2)}){src_str}: {clo['description']}\n"
            f"  → PI: {pi_str}"
        )
    return "\n".join(lines)


def _format_mapping_summary(mapping_matrix: List[Dict]) -> str:
    if not mapping_matrix:
        return "Chưa có mapping"
    summary: Dict[str, List[str]] = {}
    for m in mapping_matrix:
        clo = m.get("clo_code", "")
        plo = m.get("plo_code", "")
        if clo not in summary:
            summary[clo] = []
        if plo not in summary[clo]:
            summary[clo].append(plo)
    return "\n".join([f"{clo} → {', '.join(plos)}" for clo, plos in summary.items()])


def _format_mapping_detail(mapping_matrix: List[Dict], clo_list: List[Dict]) -> str:
    """
    Mapping chi tiết kèm Bloom level, IRMA, PI domain và justification.
    Dùng để LLM có đủ ngữ cảnh quyết định nội dung TH vs LT cho từng CLO.
    """
    if not mapping_matrix:
        return "Chưa có mapping"
    clo_lookup = {c.get("code", ""): c for c in clo_list}
    lines = []
    for m in mapping_matrix:
        clo_code = m.get("clo_code", "")
        clo      = clo_lookup.get(clo_code, {})
        bloom    = clo.get("bloom_level", "?") or "?"
        irma     = m.get("irma_level") or clo.get("mapping_level", "R") or "R"
        pi       = m.get("pi_code", "")
        plo      = m.get("plo_code", "")
        just     = (m.get("mapping_justification") or "")[:100]
        line = f"  {clo_code} [Bloom {bloom}, IRMA:{irma}] → PI:{pi} / {plo}"
        if just:
            line += f"\n    ↳ {just}"
        lines.append(line)
    return "\n".join(lines)


def _format_course_info(state: Dict, session_info: Dict, split_rationale: str = "") -> str:
    pps = session_info.get('periods_per_session', 5)
    tps = session_info.get('theory_per_session', 3)
    lps = session_info.get('lab_per_session', 2)
    rationale_line = f"\n  → Căn cứ phân bổ: {split_rationale}" if split_rationale else ""
    return (
        f"Học phần: {state.get('course_code', '')} - {state.get('course_name', '')}\n"
        f"Số tín chỉ: {session_info['credits']}\n"
        f"Tổng số buổi: {session_info['total_sessions']} buổi (= {session_info['total_sessions']} tuần)\n"
        f"Cấu trúc mỗi buổi: {pps} tiết ({tps} tiết LT + {lps} tiết TH){rationale_line}\n"
        f"Tổng tiết: {session_info['total_periods']} "
        f"(LT: {session_info['theory_periods']}, TH: {session_info['lab_periods']})"
    )


def _normalize_plan(plan: List[Dict]) -> List[Dict]:
    normalized = []
    # Tính default duration từ cặp LT/TH liền kề (no giống nhau)
    lt_dur_seen = next((s.get("duration_periods") for s in plan if s.get("type") == "LT"
                        and isinstance(s.get("duration_periods"), int) and s["duration_periods"] > 0), 3)
    th_dur_seen = next((s.get("duration_periods") for s in plan if s.get("type") == "TH"
                        and isinstance(s.get("duration_periods"), int) and s["duration_periods"] > 0), 2)
    for i, session in enumerate(plan):
        stype = session.get("type", "LT")
        default_dur = lt_dur_seen if stype == "LT" else th_dur_seen
        normalized.append({
            "no":               session.get("no", i + 1),
            "week":             session.get("week", i + 1),
            "type":             stype,
            "content":          session.get("content", f"Buổi {i + 1}"),
            "details":          session.get("details", ""),
            "clo_codes":        session.get("clo_codes", []),
            "irma_level":       session.get("irma_level", "R"),
            "activities":       session.get("activities", "Giảng giải có cấu trúc" if stype == "LT" else "Thực hành có hướng dẫn"),
            "assessment":       session.get("assessment", ""),
            "duration_periods": session.get("duration_periods") or default_dur,
        })
    return normalized


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic LT/TH split
# ─────────────────────────────────────────────────────────────────────────────

def _compute_session_split(
    clo_list: List[Dict],
    mapping_matrix: List[Dict],
    periods_per_session: int,
    theory_per_session_hint: int,
) -> Tuple[int, int, str]:
    """
    Tính tỷ lệ LT/TH tối ưu dựa trên CLO + Bloom + IRMA.

    Nguyên tắc:
    - CLO Bloom ≥ 4 (Analyze/Evaluate/Create) → thiên TH nhiều hơn
    - IRMA = M hoặc A → tăng TH
    - Bloom 1-2 + IRMA I/R → LT chủ yếu

    Returns: (theory_per_session, lab_per_session, rationale_str)
    """
    n = len(clo_list)
    if not n or periods_per_session < 2:
        lps = max(1, periods_per_session - theory_per_session_hint)
        return theory_per_session_hint, lps, "Mặc định (không có dữ liệu CLO)"

    # Gộp IRMA từ mapping_matrix (ưu tiên) rồi fallback về CLO.mapping_level
    irma_from_mapping: Dict[str, str] = {}
    for m in mapping_matrix:
        clo_code = m.get("clo_code", "")
        irma = (m.get("irma_level") or "").upper()
        if clo_code and irma in ("I", "R", "M", "A"):
            irma_from_mapping[clo_code] = irma

    bloom_total = 0
    irma_score  = 0
    irma_weights = {"I": 0, "R": 1, "M": 2, "A": 3}
    high_bloom_count = 0
    high_irma_count  = 0

    for clo in clo_list:
        code  = clo.get("code", "")
        bloom = int(clo.get("bloom_level", 2) or 2)
        irma  = irma_from_mapping.get(code) or (clo.get("mapping_level") or "R").upper()
        if irma not in irma_weights:
            irma = "R"

        bloom_total += bloom
        irma_score  += irma_weights[irma]

        if bloom >= 4:
            high_bloom_count += 1
        if irma in ("M", "A"):
            high_irma_count += 1

    avg_bloom = bloom_total / n   # 1..6
    avg_irma  = irma_score  / n   # 0..3

    # TH ratio: tuyến tính từ (Bloom≈2, IRMA≈I) → 20% TH đến (Bloom≈5, IRMA≈A) → 50% TH
    bloom_weight = max(0.0, (avg_bloom - 2.0) / 4.0)   # 0..1
    irma_weight  = avg_irma / 3.0                        # 0..1
    th_ratio = 0.20 + bloom_weight * 0.20 + irma_weight * 0.15
    th_ratio = max(0.15, min(0.55, th_ratio))

    raw_lps = round(th_ratio * periods_per_session)
    lps = max(1, min(periods_per_session - 1, raw_lps))
    tps = periods_per_session - lps

    # Build human-readable rationale
    reasons = []
    pct_high_bloom = high_bloom_count / n * 100
    pct_high_irma  = high_irma_count  / n * 100
    if pct_high_bloom >= 60:
        reasons.append(f"{pct_high_bloom:.0f}% CLO Bloom≥4 → tăng TH")
    elif pct_high_bloom <= 20:
        reasons.append(f"{100-pct_high_bloom:.0f}% CLO Bloom≤3 → tăng LT")
    if pct_high_irma >= 50:
        reasons.append(f"{pct_high_irma:.0f}% CLO IRMA=M/A → tăng TH")
    if not reasons:
        reasons.append(f"avg Bloom={avg_bloom:.1f}, avg IRMA={avg_irma:.1f} → cân bằng LT/TH")
    if tps == theory_per_session_hint:
        reasons.append("khớp cấu hình người dùng")
    elif tps != theory_per_session_hint:
        reasons.append(f"đề xuất {tps}LT+{lps}TH (người dùng chọn {theory_per_session_hint}LT)")

    return tps, lps, "; ".join(reasons)


def _generate_fallback_plan(
    clo_list: List[Dict],
    session_info: Dict,
    outline_sessions: List[Dict],
    session_clo_map: Dict[str, List[str]],
    outline_provided: bool,
) -> List[Dict]:
    """Sinh kế hoạch cơ bản khi LLM fail."""

    # PRESERVE fallback: dùng outline skeleton
    if outline_provided and outline_sessions and not is_raw_text_fallback(outline_sessions):
        logger.info("[TeachingPlan/Fallback] Dùng outline skeleton làm fallback")
        plan = []
        for i, os_item in enumerate(outline_sessions):
            no    = os_item["no"]
            clos  = session_clo_map.get(str(no), [])
            if not clos and clo_list:
                clos = [clo_list[i % len(clo_list)]["code"]]
            plan.append({
                "no":               no,
                "week":             (i // 3) + 1,
                "type":             os_item.get("session_type", "LT"),
                "content":          os_item["topic"],
                "details":          "; ".join(os_item.get("subtopics", [])),
                "clo_codes":        clos,
                "irma_level":       "I" if i < 2 else ("M" if i > len(outline_sessions) - 3 else "R"),
                "activities":       "Lab" if os_item.get("session_type") == "TH" else "Lecture",
                "assessment":       "",
                "duration_periods": os_item.get("estimated_periods", 1),
            })
        return plan

    # GENERATE fallback: sinh từ CLO list
    logger.info("[TeachingPlan/Fallback] Sinh kế hoạch cơ bản từ CLO list")
    plan = []
    total_sessions = session_info.get("total_sessions", 9)
    tps = session_info.get("theory_per_session", 3)
    lps = session_info.get("lab_per_session", 2)

    # Build CLO lookup: code → description
    clo_items = [(c["code"], c.get("description", c["code"]),
                  c.get("bloom_level", 2), c.get("mapping_level", "R"))
                 for c in clo_list] if clo_list else []
    clo_count = max(len(clo_items), 1)

    # Dành 1 buổi intro + 1 buổi tổng kết; còn lại chia đều cho CLO
    middle_sessions = max(1, total_sessions - 2)
    per_clo = max(1, middle_sessions // clo_count)

    # Hàm tính IRMA theo vị trí tiến trình
    def _irma_for(idx: int, total: int) -> str:
        pct = idx / max(total - 1, 1)
        if pct < 0.15:
            return "I"
        if pct < 0.50:
            return "R"
        if pct < 0.80:
            return "M"
        return "A"

    session_no = 1
    # Buổi 1: giới thiệu + setup môi trường
    plan.append({
        "no": session_no, "week": session_no, "type": "LT",
        "content": "Giới thiệu học phần — Tổng quan, mục tiêu và lộ trình học tập",
        "details": "Trình bày syllabus, CLO, phương pháp đánh giá; giới thiệu domain và ứng dụng thực tế",
        "clo_codes": [c[0] for c in clo_items[:2]],
        "irma_level": "I",
        "activities": "Giảng giải có cấu trúc + trao đổi kỳ vọng",
        "assessment": "A1", "duration_periods": tps,
    })
    if lps > 0:
        plan.append({
            "no": session_no, "week": session_no, "type": "TH",
            "content": "Thiết lập môi trường phát triển và làm quen công cụ",
            "details": "Cài đặt môi trường, thư viện cần thiết; chạy thử chương trình Hello-World minh họa domain",
            "clo_codes": [], "irma_level": "",
            "activities": "Thực hành có hướng dẫn",
            "assessment": "", "duration_periods": lps,
        })
    session_no += 1

    # Buổi giữa: mỗi CLO × per_clo buổi
    session_in_middle = 0
    total_middle = clo_count * per_clo
    for clo_code, clo_desc, bloom, irma_clo in clo_items:
        lt_activity = (
            "Phân tích ví dụ mẫu + thảo luận kỹ thuật" if bloom >= 4
            else "Giảng giải có cấu trúc + ví dụ mẫu"
        )
        for rep in range(per_clo):
            irma = _irma_for(session_in_middle, total_middle)
            # Nếu CLO có IRMA cụ thể và nó cao hơn → dùng
            irma_map = {"I": 0, "R": 1, "M": 2, "A": 3}
            if irma_map.get(irma_clo.upper(), 1) > irma_map.get(irma, 1):
                irma = irma_clo.upper()
            lt_content = (
                f"{clo_desc[:70]}" if rep == 0
                else f"{clo_desc[:50]} — nâng cao (phần {rep+1})"
            )
            th_content = (
                f"Thực hành: {clo_desc[:60]}"
                if rep == 0
                else f"Thực hành mở rộng: {clo_desc[:50]}"
            )
            plan.append({
                "no": session_no, "week": session_no, "type": "LT",
                "content": lt_content,
                "details": f"Bao phủ {clo_code} — xem mô tả CLO",
                "clo_codes": [clo_code],
                "irma_level": irma,
                "activities": lt_activity,
                "assessment": "", "duration_periods": tps,
            })
            if lps > 0:
                plan.append({
                    "no": session_no, "week": session_no, "type": "TH",
                    "content": th_content,
                    "details": f"Thực hành kỹ thuật tương ứng bài LT {clo_code}",
                    "clo_codes": [], "irma_level": "",
                    "activities": "Thực hành có hướng dẫn",
                    "assessment": "", "duration_periods": lps,
                })
            session_no += 1
            session_in_middle += 1

    # Buổi cuối: demo + báo cáo tổng kết
    all_clo_codes = [c[0] for c in clo_items]
    plan.append({
        "no": session_no, "week": session_no, "type": "LT",
        "content": "Tổng kết học phần — Hệ thống hóa kiến thức và hướng dẫn đánh giá cuối kỳ",
        "details": "Ôn tập toàn bộ CLO; thảo luận lỗi thường gặp, hướng phát triển; hướng dẫn ôn thi",
        "clo_codes": all_clo_codes,
        "irma_level": "A",
        "activities": "Phân tích ví dụ mẫu + thảo luận kỹ thuật",
        "assessment": "", "duration_periods": tps,
    })
    if lps > 0:
        plan.append({
            "no": session_no, "week": session_no, "type": "TH",
            "content": "Demo sản phẩm cuối kỳ và báo cáo nhóm",
            "details": "Sinh viên trình diễn sản phẩm/kết quả dự án, nhận phản hồi từ GV và nhóm khác",
            "clo_codes": [], "irma_level": "",
            "activities": "Báo cáo kỹ thuật + trình diễn sản phẩm + phản hồi học thuật",
            "assessment": "A3", "duration_periods": lps,
        })

    return plan
