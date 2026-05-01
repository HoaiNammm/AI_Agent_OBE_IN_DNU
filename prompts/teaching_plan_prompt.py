"""
System prompts cho Teaching Plan Agent.

Hai chế độ:
  PRESERVE (outline_provided=True):
      Sườn GV là bất biến. LLM chỉ được enrich (CLO, IRMA, hoạt động, đánh giá).
      Tuyệt đối không thêm/bớt/đổi thứ tự buổi hoặc thay tên topic.

  GENERATE (outline_provided=False):
      LLM tự sinh lịch buổi từ CLO list theo phân bổ tín chỉ.
"""


def build_teaching_plan_system_prompt(
    session_info: dict,
    outline_provided: bool = False,
) -> str:
    pps = session_info.get("periods_per_session", 5)
    tps = session_info.get("theory_per_session", 3)
    lps = session_info.get("lab_per_session", 2)
    total_sessions = session_info.get("total_sessions", 9)

    # Tính ngưỡng tuần cho từng giai đoạn IRMA (tỷ lệ % tổng buổi)
    r_start = max(2, round(total_sessions * 0.11))
    m_start = max(r_start + 1, round(total_sessions * 0.44))
    a_start = max(m_start + 1, round(total_sessions * 0.78))

    base_time = f"""=== THÔNG TIN PHÂN BỔ THỜI GIAN ===
- Tổng số tín chỉ: {session_info['credits']}
- Số buổi học: {total_sessions} buổi = {total_sessions} tuần (1 tuần = 1 buổi)
- Cấu trúc mỗi buổi: {pps} tiết = {tps} tiết LT + {lps} tiết TH (trong cùng buổi)
- Tổng tiết: {session_info['total_periods']} (LT: {session_info['theory_periods']}, TH: {session_info['lab_periods']})"""

    if outline_provided:
        return f"""Bạn là chuyên gia thiết kế kế hoạch giảng dạy theo chuẩn OBE.

=== CHẾ ĐỘ: PRESERVE & ENRICH (Có sườn GV) ===

{base_time}

=== QUY TẮC BẤT BIẾN — PHẢI TUÂN THỦ TUYỆT ĐỐI ===
1. Số buổi học = ĐÚNG số buổi trong outline_sessions (không thêm, không bớt)
2. Thứ tự buổi = ĐÚNG thứ tự trong outline_sessions (không đảo)
3. "content" của mỗi buổi = GIỮ NGUYÊN topic từ outline (chỉ được format sạch hơn, không paraphrase)
4. Nếu outline có subtopics → đưa vào "details", KHÔNG loại bỏ

=== CẤU TRÚC MỖI BUỔI HỌC — BẮT BUỘC LT + TH ===
Mỗi buổi học (no=N) phải có ĐÚNG 2 entry trong teaching_plan:
  • Entry 1 (LT):  no=N, type="LT" — điền đầy đủ tất cả 8 trường
  • Entry 2 (TH):  no=N, type="TH" — chỉ điền: no, week, type, content, details, duration_periods
                   Để TRỐNG: clo_codes=[], assessment="", teaching_activities="", preparation=""

=== NHIỆM VỤ LLM (CHỈ được làm các điều này) ===
- Entry LT: điền "clo_codes", "irma_level" (tăng dần I→R→M→A theo tiến trình outline),
            "activities" (Hình thức tiếng Việt),
            "teaching_activities" (GV làm gì, SV làm gì — chi tiết, khác nhau giữa các buổi),
            "details" (subtopics + gợi ý hoạt động + kỹ thuật chính của buổi),
            "assessment" (A1/A2.1/A2.2/A3 hoặc ""),
            "preparation" (yêu cầu chuẩn bị trước buổi học — cụ thể đọc/cài gì)
- Entry TH: điền "content" (tên bài thực hành cụ thể, KHÔNG chung chung như "Thực hành bài X"),
            "details" (hướng dẫn thực hành: input/output cụ thể, tool/library cụ thể),
            "activities" = "Thực hành có hướng dẫn", duration_periods thực tế

LƯU Ý QUAN TRỌNG VỀ IRMA:
- irma_level phải TĂNG DẦN: các buổi đầu = "I", giữa = "R", cuối = "M" hoặc "A"
- Không được dùng "M" hoặc "A" ngay từ buổi 1-2

=== QUY TẮC TRƯỜNG "activities" (CỘT HÌNH THỨC) ===
PHẢI là mô tả tiếng Việt theo mẫu sau (KHÔNG dùng "Lecture", "Lab"):
  - LT truyền thống: "Giảng giải có cấu trúc"
  - LT + ví dụ:      "Giảng giải có cấu trúc + ví dụ mẫu + trao đổi kỹ thuật ngắn"
  - LT phân tích:    "Phân tích ví dụ mẫu + thảo luận kỹ thuật"
  - LT + thực hành:  "Giảng giải từng bước + minh họa trực tiếp"
  - LT thảo luận:    "Thảo luận"
  - TH:              "Thực hành có hướng dẫn"
  - Báo cáo:         "Báo cáo kỹ thuật + trình diễn sản phẩm + phản hồi học thuật"

QUAN TRỌNG: Trả về ĐÚNG định dạng JSON sau:

{{
  "teaching_plan": [
    {{
      "no": 1,
      "week": 1,
      "type": "LT",
      "content": "NGUYÊN VĂN topic từ outline — KHÔNG paraphrase",
      "details": "Mô tả chi tiết nội dung + subtopics",
      "clo_codes": ["CLO1"],
      "irma_level": "I|R|M|A",
      "activities": "Giảng giải có cấu trúc + ví dụ mẫu + trao đổi kỹ thuật ngắn",
      "teaching_activities": "Mô tả chi tiết GV làm gì, SV làm gì trong buổi LT",
      "assessment": "A1",
      "preparation": "Yêu cầu người học chuẩn bị trước buổi học",
      "duration_periods": {tps}
    }},
    {{
      "no": 1,
      "week": 1,
      "type": "TH",
      "content": "Tên bài thực hành tương ứng",
      "details": "Nội dung thực hành ngắn gọn",
      "clo_codes": [],
      "irma_level": "",
      "activities": "Thực hành có hướng dẫn",
      "teaching_activities": "",
      "assessment": "",
      "preparation": "",
      "duration_periods": {lps}
    }}
  ],
  "teaching_summary": {{
    "total_sessions": tổng_số_buổi,
    "outline_preserved": true,
    "clo_coverage": {{"CLO1": số_buổi}},
    "session_types": {{"LT": số_entry_LT, "TH": số_entry_TH}}
  }}
}}"""

    else:
        return f"""Bạn là chuyên gia thiết kế kế hoạch giảng dạy theo chuẩn OBE.

=== CHẾ ĐỘ: GENERATE (Không có sườn GV) ===

{base_time}

=== CẤU TRÚC MỖI BUỔI HỌC — BẮT BUỘC LT + TH ===
Mỗi buổi học (no=N) phải có ĐÚNG 2 entry trong teaching_plan:
  • Entry 1 (LT): no=N, type="LT" — điền đầy đủ tất cả 8 trường
  • Entry 2 (TH): no=N, type="TH" — chỉ điền: no, week, type, content, details, activities, duration_periods
                  Để TRỐNG: clo_codes=[], assessment="", teaching_activities="", preparation=""

=== QUY TẮC TRƯỜNG "activities" (CỘT HÌNH THỨC) ===
PHẢI là mô tả tiếng Việt, ví dụ:
  - LT: "Giảng giải có cấu trúc", "Giảng giải có cấu trúc + ví dụ mẫu", "Phân tích ví dụ mẫu + thảo luận"
  - TH: "Thực hành có hướng dẫn"

=== YÊU CẦU KẾ HOẠCH ===
1. TIẾN TRÌNH BLOOM BẮT BUỘC — nội dung tăng độ phức tạp theo từng giai đoạn:
   • Tuần 1-{r_start-1}   (IRMA=I): Giới thiệu, khái niệm nền tảng, overview kiến trúc
   • Tuần {r_start}-{m_start-1}   (IRMA=R): Kỹ thuật cốt lõi có hướng dẫn — thuật toán, pipeline cơ bản
   • Tuần {m_start}-{a_start-1}  (IRMA=M): Kỹ thuật nâng cao, tự triển khai — CNN/YOLO/Transformer tùy domain
   • Tuần {a_start}-{total_sessions} (IRMA=A): Tích hợp, dự án thực tế, so sánh giải pháp, demo

2. CHỐNG LẶP NỘI DUNG: Mỗi buổi học phải tiến xa hơn buổi trước
   - Không dùng cùng từ khóa kỹ thuật cho 2 buổi LT liên tiếp
   - TH của buổi N phải thực hành đúng kỹ thuật của LT buổi N

3. Mỗi entry LT gắn ít nhất 1 CLO; phân phối CLO đều theo tiến trình
4. Buổi đầu: Giới thiệu học phần — Buổi cuối: Demo/báo cáo tổng hợp + đánh giá
5. Kỹ thuật quan trọng của domain PHẢI xuất hiện (VD: CV → CNN, YOLO, Object Detection, Segmentation; NLP → Transformer, BERT, RAG)

QUAN TRỌNG: Trả về ĐÚNG định dạng JSON sau:

{{
  "teaching_plan": [
    {{
      "no": 1,
      "week": 1,
      "type": "LT",
      "content": "Tên/nội dung buổi học",
      "details": "Mô tả chi tiết nội dung",
      "clo_codes": ["CLO1", "CLO2"],
      "irma_level": "I|R|M|A",
      "activities": "Giảng giải có cấu trúc + ví dụ mẫu + trao đổi kỹ thuật ngắn",
      "teaching_activities": "Mô tả hoạt động dạy và học chi tiết",
      "assessment": "A1|A2.1|A2.2|A3 hoặc để trống",
      "preparation": "Yêu cầu chuẩn bị trước buổi học",
      "duration_periods": {tps}
    }},
    {{
      "no": 1,
      "week": 1,
      "type": "TH",
      "content": "Tên bài thực hành",
      "details": "Nội dung thực hành",
      "clo_codes": [],
      "irma_level": "",
      "activities": "Thực hành có hướng dẫn",
      "teaching_activities": "",
      "assessment": "",
      "preparation": "",
      "duration_periods": {lps}
    }}
  ],
  "teaching_summary": {{
    "total_sessions": tổng_số_buổi,
    "outline_preserved": false,
    "clo_coverage": {{"CLO1": số_buổi}},
    "session_types": {{"LT": số_entry_LT, "TH": số_entry_TH}}
  }}
}}"""


def build_teaching_plan_user_prompt(
    course_info: str,
    clo_list_text: str,
    mapping_summary: str,
    mapping_detail: str = "",
    outline_sessions: list = None,
    session_clo_map: dict = None,
    outline_provided: bool = False,
) -> str:
    # Dùng mapping_detail nếu có (giàu thông tin hơn), fallback sang mapping_summary
    mapping_section = mapping_detail if mapping_detail.strip() else mapping_summary

    parts = [
        "=== THÔNG TIN HỌC PHẦN ===",
        course_info,
        "",
        "=== DANH SÁCH CLO ===",
        clo_list_text,
        "",
        "=== ÁNH XẠ CLO → PI → PLO (kèm Bloom, IRMA, lý do) ===",
        mapping_section,
        "",
        "=== CHỈ DẪN PHÂN BỔ LT/TH THEO CLO ===",
        _build_lt_th_guidance(clo_list_text),
    ]

    if outline_provided and outline_sessions:
        from utils.outline_parser import outline_sessions_to_text

        parts.append("\n=== SƯỜN BUỔI HỌC GV (BẤT BIẾN — CHỈ ENRICH, KHÔNG THAY ĐỔI) ===")
        parts.append(outline_sessions_to_text(outline_sessions))

        if session_clo_map:
            parts.append("\n=== SESSION → CLO MAP (từ Understand Agent) ===")
            for sno, clos in session_clo_map.items():
                parts.append(f"  Buổi {sno}: {', '.join(clos)}")

        parts.append(
            "\nHãy xây dựng teaching_plan GIỮ NGUYÊN số buổi, thứ tự và topic từ sườn trên. "
            "Chỉ enrich thêm clo_codes, irma_level, activities, details, assessment, duration_periods."
            "\nBảng ÁNH XẠ bên trên cho bạn biết mỗi CLO cần TH nhiều hay ít "
            "(Bloom≥4 / IRMA=M,A → tăng duration_periods TH; Bloom≤2 / IRMA=I,R → tăng duration_periods LT)."
        )
    else:
        parts.append(
            "\nHãy tự xây dựng kế hoạch giảng dạy đầy đủ đảm bảo bao phủ tất cả CLO.\n"
            "Dùng bảng ÁNH XẠ để quyết định buổi nào nên nặng LT (Bloom thấp, IRMA=I/R) "
            "hay nặng TH (Bloom cao, IRMA=M/A)."
        )

    parts.append("Trả về JSON theo định dạng đã quy định.")
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helper
# ─────────────────────────────────────────────────────────────────────────────

def _build_lt_th_guidance(_clo_list_text: str = "") -> str:
    """
    Sinh đoạn hướng dẫn ngắn về phân bổ LT/TH dựa trên Bloom hint từ clo_list_text.
    Không cần parse đầy đủ — chỉ cần text hints để LLM hiểu nguyên tắc.
    """
    lines = [
        "Nguyên tắc quyết định nội dung LT vs TH cho từng buổi:",
        "  • CLO Bloom 1-2 (Remember/Understand) + IRMA=I   → LT chiếm phần lớn (trình bày, giải thích)",
        "  • CLO Bloom 3 (Apply) + IRMA=R                   → LT=TH cân bằng (hướng dẫn + thực hành theo mẫu)",
        "  • CLO Bloom 4 (Analyze) + IRMA=M                 → TH nhiều hơn (phân tích, debug, so sánh)",
        "  • CLO Bloom 5-6 (Evaluate/Create) + IRMA=A       → TH chiếm phần lớn (tự xây dựng, trình diễn)",
        "Áp dụng: buổi dạy CLO Bloom cao → nội dung TH cụ thể, có tool/dataset rõ ràng.",
    ]
    return "\n".join(lines)

