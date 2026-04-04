"""
OBE Utilities - Dữ liệu chuẩn OBE/AUN-QA cho Khoa CNTT - ĐH Đà Nẵng
Bao gồm: Bloom Taxonomy, PLO, PI, IRMA levels và các helper functions
"""

from typing import Dict, List, Tuple

# ============================================================
# BLOOM'S TAXONOMY
# ============================================================

BLOOM_LEVELS = {
    1: "Remember",
    2: "Understand",
    3: "Apply",
    4: "Analyze",
    5: "Evaluate",
    6: "Create",
}

BLOOM_VERBS: Dict[int, List[str]] = {
    1: [
        "define", "list", "recall", "recognize", "state", "identify", "name", "repeat",
        "nhớ lại", "liệt kê", "nhận biết", "xác định", "nêu", "ghi nhớ",
    ],
    2: [
        "explain", "describe", "summarize", "classify", "interpret", "paraphrase",
        "giải thích", "mô tả", "tóm tắt", "phân loại", "diễn giải", "trình bày",
    ],
    3: [
        "apply", "use", "implement", "solve", "demonstrate", "execute", "perform",
        "áp dụng", "sử dụng", "thực hiện", "giải", "lập trình", "triển khai", "xây dựng",
    ],
    4: [
        "analyze", "compare", "differentiate", "examine", "decompose", "distinguish",
        "phân tích", "so sánh", "phân biệt", "kiểm tra", "phân rã", "đánh giá chi tiết",
    ],
    5: [
        "evaluate", "judge", "assess", "critique", "justify", "argue",
        "đánh giá", "nhận xét", "phê bình", "chứng minh", "lựa chọn", "phán xét",
    ],
    6: [
        "design", "build", "create", "formulate", "develop", "construct", "compose",
        "thiết kế", "tạo ra", "lập", "phát triển", "xây dựng hệ thống", "đề xuất",
    ],
}

BLOOM_LEVEL_VI = {
    1: "Nhớ (Remember)",
    2: "Hiểu (Understand)",
    3: "Áp dụng (Apply)",
    4: "Phân tích (Analyze)",
    5: "Đánh giá (Evaluate)",
    6: "Sáng tạo (Create)",
}


def get_bloom_level(verb: str) -> Tuple[int, str]:
    """Xác định mức Bloom từ động từ. Trả về (level_number, level_name_vi)."""
    verb_lower = verb.lower()
    for level, verbs in BLOOM_VERBS.items():
        if any(v in verb_lower for v in verbs):
            return level, BLOOM_LEVEL_VI[level]
    return 2, BLOOM_LEVEL_VI[2]  # default: Understand


def get_bloom_verbs_for_level(level: int) -> List[str]:
    """Lấy danh sách động từ Bloom cho mức cho trước."""
    return BLOOM_VERBS.get(level, BLOOM_VERBS[2])


# ============================================================
# PLO - PROGRAM LEARNING OUTCOMES
# Khoa Công nghệ Thông tin - ĐH Đà Nẵng (Chuẩn AUN-QA / ABET)
# ============================================================

PLO_DATA: Dict[str, str] = {
    "PLO1": "Áp dụng được kiến thức nền tảng về toán học, khoa học và công nghệ thông tin để giải quyết các bài toán kỹ thuật phần mềm",
    "PLO2": "Phân tích được yêu cầu, xác định và phát biểu bài toán trong lĩnh vực công nghệ thông tin",
    "PLO3": "Thiết kế, cài đặt và đánh giá được hệ thống phần mềm đáp ứng các yêu cầu đặc tả kỹ thuật",
    "PLO4": "Áp dụng được các kỹ thuật, công cụ và phương pháp hiện đại trong phát triển phần mềm",
    "PLO5": "Giao tiếp hiệu quả bằng văn bản và lời nói trong môi trường kỹ thuật và phi kỹ thuật",
    "PLO6": "Làm việc hiệu quả trong nhóm đa ngành, đảm nhận các vai trò khác nhau kể cả vai trò lãnh đạo",
    "PLO7": "Hiểu được trách nhiệm nghề nghiệp, xã hội, pháp lý và đạo đức trong lĩnh vực CNTT",
    "PLO8": "Nhận thức và thực hành học tập suốt đời để cập nhật kiến thức trong lĩnh vực CNTT phát triển nhanh",
    "PLO9": "Hiểu tác động của giải pháp kỹ thuật trong bối cảnh toàn cầu, kinh tế, môi trường và xã hội",
    "PLO10": "Nắm bắt và phân tích các vấn đề, xu hướng đương đại trong lĩnh vực công nghệ thông tin",
}

# ============================================================
# PI - PERFORMANCE INDICATORS
# Mỗi PLO có từ 2-4 PI cụ thể, đo lường được
# ============================================================

PI_DATA: Dict[str, Dict[str, str]] = {
    "PLO1": {
        "PI1.1": "Áp dụng kiến thức toán học (đại số tuyến tính, xác suất thống kê, toán rời rạc) vào phân tích và giải quyết bài toán CNTT",
        "PI1.2": "Sử dụng kiến thức về cấu trúc dữ liệu và giải thuật để lựa chọn và tối ưu hóa giải pháp",
        "PI1.3": "Ứng dụng lý thuyết về hệ thống, mạng và kiến trúc máy tính trong thiết kế giải pháp",
    },
    "PLO2": {
        "PI2.1": "Thu thập, phân tích và đặc tả yêu cầu người dùng từ các tình huống thực tế",
        "PI2.2": "Mô hình hóa bài toán bằng các ký hiệu, biểu đồ chuẩn (UML, flowchart, ER diagram)",
        "PI2.3": "Xác định ràng buộc, điều kiện giới hạn và đề xuất các tiêu chí chấp nhận giải pháp",
    },
    "PLO3": {
        "PI3.1": "Thiết kế kiến trúc hệ thống phần mềm theo các mô hình chuẩn (MVC, microservices, layered)",
        "PI3.2": "Cài đặt, kiểm thử và tích hợp phần mềm theo quy trình kỹ thuật chuyên nghiệp",
        "PI3.3": "Đánh giá chất lượng phần mềm theo các tiêu chí kỹ thuật và nghiệp vụ",
    },
    "PLO4": {
        "PI4.1": "Sử dụng thành thạo các IDE, framework và công cụ phát triển phần mềm hiện đại",
        "PI4.2": "Áp dụng các phương pháp phát triển phần mềm linh hoạt (Agile, Scrum, DevOps)",
        "PI4.3": "Sử dụng công cụ kiểm thử tự động, quản lý mã nguồn (Git) và CI/CD pipeline",
    },
    "PLO5": {
        "PI5.1": "Viết tài liệu kỹ thuật (đặc tả, thiết kế, hướng dẫn) rõ ràng và chính xác",
        "PI5.2": "Trình bày và bảo vệ giải pháp kỹ thuật trước nhóm chuyên gia và người dùng",
        "PI5.3": "Giao tiếp hiệu quả với khách hàng và các bên liên quan không có nền tảng kỹ thuật",
    },
    "PLO6": {
        "PI6.1": "Đóng góp tích cực và chủ động trong nhóm dự án phần mềm đa thành viên",
        "PI6.2": "Sử dụng các công cụ cộng tác (Git, Jira, Trello) để quản lý và phối hợp công việc nhóm",
        "PI6.3": "Thể hiện khả năng lãnh đạo, phân công và điều phối công việc trong nhóm dự án",
    },
    "PLO7": {
        "PI7.1": "Nhận diện và xử lý các tình huống có xung đột đạo đức nghề nghiệp trong CNTT",
        "PI7.2": "Tôn trọng bản quyền phần mềm, quyền riêng tư dữ liệu và an toàn thông tin",
        "PI7.3": "Tuân thủ các quy định pháp lý và tiêu chuẩn nghề nghiệp trong phát triển phần mềm",
    },
    "PLO8": {
        "PI8.1": "Chủ động tự học công nghệ mới thông qua tài liệu, khóa học online và cộng đồng kỹ thuật",
        "PI8.2": "Phản ánh và cải thiện kỹ năng chuyên môn dựa trên phản hồi và kinh nghiệm thực tế",
    },
    "PLO9": {
        "PI9.1": "Phân tích tác động kinh tế, xã hội của giải pháp phần mềm đối với người dùng và cộng đồng",
        "PI9.2": "Xem xét các yếu tố bền vững, hiệu quả năng lượng trong thiết kế và vận hành hệ thống",
    },
    "PLO10": {
        "PI10.1": "Nắm bắt và phân tích các xu hướng công nghệ mới (AI/ML, Cloud, IoT, Blockchain, Cybersecurity)",
        "PI10.2": "Đánh giá tác động của chuyển đổi số và công nghệ mới tới các lĩnh vực kinh tế - xã hội",
    },
}

# ============================================================
# IRMA LEVELS
# ============================================================

IRMA_LEVELS = {
    "I": "Introduce - Giới thiệu khái niệm, mức độ nhận biết cơ bản",
    "R": "Reinforce - Củng cố, luyện tập với sự hỗ trợ",
    "M": "Master - Thành thạo, thực hiện độc lập",
    "A": "Apply - Áp dụng sáng tạo vào tình huống mới",
}

IRMA_BLOOM_MAP = {
    "I": [1, 2],       # Remember, Understand
    "R": [2, 3],       # Understand, Apply
    "M": [3, 4],       # Apply, Analyze
    "A": [4, 5, 6],    # Analyze, Evaluate, Create
}


def suggest_irma_for_bloom(bloom_level: int) -> str:
    """Gợi ý mức IRMA phù hợp với mức Bloom."""
    if bloom_level <= 2:
        return "I"
    elif bloom_level == 3:
        return "R"
    elif bloom_level == 4:
        return "M"
    else:
        return "A"


# ============================================================
# CREDIT SYSTEM (Hệ thống tín chỉ Việt Nam)
# 1 tín chỉ lý thuyết = 15 tiết học
# 1 tín chỉ thực hành = 30 tiết học (15 buổi × 2 tiết)
# ============================================================

def calculate_sessions(credits: str, theory_ratio: float = 0.7) -> Dict:
    """
    Tính số buổi học dựa theo số tín chỉ.
    
    Args:
        credits: Số tín chỉ (str, vd "3")
        theory_ratio: Tỷ lệ lý thuyết (0.7 = 70% LT, 30% TH)
    
    Returns:
        Dict với total_sessions, theory_sessions, lab_sessions, weeks
    """
    try:
        c = int(credits)
    except (ValueError, TypeError):
        c = 3

    # 1 tín chỉ = 15 tiết → 1 buổi = 1 tiết (hoặc 2 tiết tùy trường)
    # Tại ĐH Đà Nẵng: 1 tín chỉ ≈ 15 tiết = 15 buổi 50 phút
    total_periods = c * 15
    theory_periods = round(total_periods * theory_ratio)
    lab_periods = total_periods - theory_periods

    return {
        "credits": c,
        "total_periods": total_periods,
        "theory_periods": theory_periods,
        "lab_periods": lab_periods,
        "total_sessions": total_periods,  # 1 buổi = 1 tiết
        "weeks": c * 5,  # ~5 tuần / tín chỉ
    }


# ============================================================
# ASSESSMENT WEIGHTS (Trọng số đánh giá chuẩn)
# ============================================================

DEFAULT_ASSESSMENT_WEIGHTS = {
    "A1": {
        "name": "Đánh giá quá trình",
        "description": "Chuyên cần, bài tập, quiz, thảo luận",
        "weight": 0.10,
    },
    "A2.1": {
        "name": "Kiểm tra giữa kỳ",
        "description": "Kiểm tra lý thuyết giữa học kỳ (trắc nghiệm/tự luận)",
        "weight": 0.20,
    },
    "A2.2": {
        "name": "Thực hành / Bài tập lớn",
        "description": "Bài thực hành, dự án nhóm, báo cáo",
        "weight": 0.30,
    },
    "A3": {
        "name": "Thi cuối kỳ",
        "description": "Thi cuối học kỳ (lý thuyết + thực hành)",
        "weight": 0.40,
    },
}


# ============================================================
# PLO-PI HELPER FUNCTIONS
# ============================================================

def get_all_pi_codes() -> List[str]:
    """Lấy tất cả mã PI."""
    codes = []
    for plo, pis in PI_DATA.items():
        codes.extend(pis.keys())
    return codes


def get_pi_description(pi_code: str) -> str:
    """Lấy mô tả của PI theo mã."""
    for plo, pis in PI_DATA.items():
        if pi_code in pis:
            return pis[pi_code]
    return ""


def get_plo_for_pi(pi_code: str) -> str:
    """Xác định PLO chứa PI này."""
    for plo, pis in PI_DATA.items():
        if pi_code in pis:
            return plo
    return ""


def get_pi_list_text() -> str:
    """Trả về danh sách PI dạng text để đưa vào prompt LLM."""
    lines = []
    for plo_code, pis in PI_DATA.items():
        plo_desc = PLO_DATA.get(plo_code, "")
        lines.append(f"\n{plo_code}: {plo_desc}")
        for pi_code, pi_desc in pis.items():
            lines.append(f"  {pi_code}: {pi_desc}")
    return "\n".join(lines)


def get_plo_list_text() -> str:
    """Trả về danh sách PLO dạng text để đưa vào prompt LLM."""
    lines = []
    for plo_code, desc in PLO_DATA.items():
        lines.append(f"{plo_code}: {desc}")
    return "\n".join(lines)
