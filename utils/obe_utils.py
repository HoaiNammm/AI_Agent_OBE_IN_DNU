"""
OBE Utilities - Dữ liệu chuẩn OBE/AUN-QA cho Khoa CNTT - ĐH Đà Nẵng
Bao gồm: Bloom Taxonomy, PLO, PI, IRMA levels và các helper functions
"""

from typing import Dict, List, Optional, Tuple
from kb.plo_pi_loader import _DATA as _KB_DATA

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
        "fine-tune", "finetune", "prompt", "prompting", "huấn luyện", "tinh chỉnh",
        "áp dụng", "sử dụng", "thực hiện", "giải", "lập trình", "triển khai", "xây dựng",
        "cài đặt", "lập trình", "viết code", "hiện thực",
    ],
    4: [
        "analyze", "compare", "differentiate", "examine", "decompose", "distinguish",
        "benchmark", "ablation",
        "phân tích", "so sánh", "phân biệt", "kiểm tra", "phân rã", "đánh giá chi tiết",
        "tối ưu", "gỡ lỗi", "chẩn đoán", "điều chỉnh tham số",
    ],
    5: [
        "evaluate", "judge", "assess", "critique", "justify", "argue",
        "đánh giá", "nhận xét", "phê bình", "chứng minh", "lựa chọn", "phán xét",
        "biện minh", "lựa chọn mô hình", "so sánh mô hình",
    ],
    6: [
        "design", "build", "create", "formulate", "develop", "construct", "compose",
        "architect", "pipeline", "rag", "orchestrate", "engineer",
        "thiết kế", "tạo ra", "lập", "phát triển", "xây dựng hệ thống", "đề xuất",
        "kiến trúc", "xây dựng pipeline", "thiết kế hệ thống", "đề xuất giải pháp",
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
    """
    Xác định mức Bloom từ động từ. Trả về (level_number, level_name_vi).
    Duyệt từ cao xuống thấp (6→1) để ưu tiên match dài/cụ thể hơn:
    "xây dựng pipeline" → Bloom 6 (không phải Bloom 3 vì "xây dựng" là substring).
    """
    verb_lower = verb.lower()
    # Sắp xếp từ cao đến thấp; trong mỗi level, ưu tiên verb dài trước
    for level in sorted(BLOOM_VERBS.keys(), reverse=True):
        verbs_sorted = sorted(BLOOM_VERBS[level], key=len, reverse=True)
        if any(v in verb_lower for v in verbs_sorted):
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
# Single source of truth: loaded from KB_PLO_PI_Matrix_1.md via plo_pi_loader
# ============================================================

PI_DATA: Dict[str, Dict[str, str]] = _KB_DATA["KHMT"]["pi"]  # KHMT = most comprehensive shared base


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

def calculate_sessions(
    credits: str,
    theory_ratio: float = 0.7,
    periods_per_session: int = 5,
    theory_per_session: int = 3,
) -> Dict:
    """
    Tính số buổi học dựa theo số tín chỉ.

    Mô hình lịch học:
        - 1 tuần = 1 buổi cho học phần này.
        - Mỗi buổi = `periods_per_session` tiết (mặc định 5 tiết).
        - Chia trong buổi: `theory_per_session` tiết LT + còn lại TH.

    Args:
        credits             : Số tín chỉ (str, vd "3")
        theory_ratio        : Không dùng để tách LT/TH nữa; giữ lại cho khả năng tương thích.
        periods_per_session : Tổng số tiết mỗi buổi (mặc định 5).
        theory_per_session  : Số tiết LT trong mỗi buổi (mặc định 3).
    """
    try:
        c = int(credits)
    except (ValueError, TypeError):
        c = 3

    periods_per_session = max(2, int(periods_per_session))
    theory_per_session  = max(1, min(theory_per_session, periods_per_session - 1))
    lab_per_session     = periods_per_session - theory_per_session

    # Tổng tiết theo tín chỉ (1 TC = 15 tiết chuẩn)
    total_periods_raw = c * 15
    # Số buổi = tổng tiết ÷ số tiết/buổi
    total_sessions = max(1, total_periods_raw // periods_per_session)

    return {
        "credits":              c,
        "total_periods":        total_sessions * periods_per_session,
        "theory_periods":       theory_per_session * total_sessions,
        "lab_periods":          lab_per_session    * total_sessions,
        "total_sessions":       total_sessions,
        "weeks":                total_sessions,      # 1 buổi/tuần
        "periods_per_session":  periods_per_session,
        "theory_per_session":   theory_per_session,
        "lab_per_session":      lab_per_session,
    }


# ============================================================
# ASSESSMENT WEIGHTS (Trọng số đánh giá chuẩn)
# ============================================================

DEFAULT_ASSESSMENT_WEIGHTS = {
    "A1": {
        "name": "Đánh giá chuyên cần",
        "description": "Điểm danh, theo dõi tham gia và chuẩn bị bài",
        "format": "Điểm danh, theo dõi tham gia và chuẩn bị bài",
        "criteria_summary": "Mức độ tham dự, chuẩn bị, tham gia và tuân thủ quy định lớp học",
        "weight": 0.10,
    },
    "A2.1": {
        "name": "Đánh giá giữa kỳ 1",
        "description": "Bài thực hành hoặc báo cáo ngắn",
        "format": "Bài thực hành hoặc báo cáo ngắn",
        "criteria_summary": "Đánh giá CLO giai đoạn đầu học phần theo nội dung và metric phù hợp",
        "weight": 0.15,
    },
    "A2.2": {
        "name": "Đánh giá giữa kỳ 2",
        "description": "Bài thực hành hoặc báo cáo ngắn",
        "format": "Bài thực hành hoặc báo cáo ngắn",
        "criteria_summary": "Đánh giá CLO giai đoạn giữa-cuối học phần; so sánh và biện minh lựa chọn",
        "weight": 0.15,
    },
    "A3": {
        "name": "Đánh giá cuối kỳ",
        "description": "Bài tập lớn/dự án có demo",
        "format": "Bài tập lớn/dự án có demo",
        "criteria_summary": "Giải pháp hoạt động; chất lượng đầu ra; diễn giải kết quả; bộ minh chứng đầy đủ",
        "weight": 0.60,
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


def get_plo_list_text(program: str = "GENERIC") -> str:
    """Trả về danh sách PLO dạng text để đưa vào prompt LLM."""
    data = PROGRAM_DATA.get(program, PROGRAM_DATA["GENERIC"])["plo"] if "PROGRAM_DATA" in globals() else PLO_DATA
    lines = []
    for plo_code, desc in data.items():
        lines.append(f"{plo_code}: {desc}")
    return "\n".join(lines)


# ============================================================
# SHARED PLOs / PIs (PLO1, PLO2, PLO3, PLO7, PLO8, PLO9, PLO12)
# Dùng chung cho cả 3 ngành CNTT / HTTT / KHMT
# Nguồn: KB_PLO_PI_Matrix.md (05/2026)
# ============================================================

_SHARED_PLO_DATA: Dict[str, str] = {
    "PLO1":  "Hiểu rõ các nguyên lý cơ bản của chủ nghĩa Mác - Lênin, đường lối cách mạng của Đảng Cộng sản Việt Nam, tư tưởng Hồ Chí Minh; chính sách, pháp luật của Nhà nước",
    "PLO2":  "Vận dụng kiến thức về Khoa học tự nhiên, Xã hội, Ngoại ngữ, Tin học vào lĩnh vực chuyên môn, nghề nghiệp",
    "PLO3":  "Hoàn thành kiến thức Quốc phòng - an ninh và Giáo dục thể chất để tự rèn luyện về tinh thần và sức khỏe tốt",
    "PLO7":  "Vận dụng tốt các kỹ năng: giao tiếp, thuyết trình, đàm phán, xác định mục tiêu và lập kế hoạch, xử lý linh hoạt các tình huống trong lĩnh vực chuyên môn",
    "PLO8":  "Có kỹ năng làm việc nhóm, tư duy hệ thống, phân tích, phản biện, tổng hợp, dự báo, quản lý, dẫn dắt và giải quyết vấn đề trong các hoạt động chuyên môn",
    "PLO9":  "Sử dụng được Tiếng Anh cơ bản, tin học văn phòng, tin học ứng dụng trong lĩnh vực chuyên môn",
    "PLO12": "Có phẩm chất đạo đức nghề nghiệp, tinh thần học tập nghiêm túc, năng lực nghiên cứu độc lập, tư duy sáng tạo, thích nghi nhanh với sự thay đổi của môi trường, có khả năng định hướng và tìm kiếm cơ hội phát triển nghề nghiệp, thực hiện tốt trách nhiệm công dân",
}

_SHARED_PI_DATA: Dict[str, Dict[str, str]] = {
    "PLO1": {
        "PI1.1": "Hiểu rõ các kiến thức cơ bản một cách hệ thống, xây dựng thế giới quan, nhân sinh quan, phương pháp luận khoa học và nền tảng cơ sở lý luận",
        "PI1.2": "Hiểu rõ chủ trương, đường lối của Đảng, chính sách, pháp luật của Nhà nước",
    },
    "PLO2": {
        "PI2.1": "Vận dụng các kiến thức cơ bản của khoa học tự nhiên, xã hội để hình thành tư duy khoa học",
        "PI2.2": "Vận dụng các kiến thức Tin học, Ngoại ngữ để hỗ trợ các hoạt động chuyên môn",
    },
    "PLO3": {
        "PI3.1": "Hiểu rõ các kiến thức Quốc phòng toàn dân & An ninh nhân dân",
        "PI3.2": "Hiểu được các kiến thức giáo dục thể chất để rèn luyện sức khỏe thể chất và tinh thần",
    },
    "PLO7": {
        "PI7.1": "Truyền đạt được những vấn đề chuyên môn, giúp các bên liên quan đạt đến thống nhất",
        "PI7.2": "Xử lý linh hoạt các tình huống phát sinh trong quá trình giao tiếp, làm việc",
    },
    "PLO8": {
        "PI8.1": "Phân tích tình huống, phát hiện và tổng hợp các vấn đề trong lĩnh vực chuyên môn",
        "PI8.2": "Thể hiện tư duy hệ thống để giải quyết vấn đề trong lĩnh vực chuyên môn",
    },
    "PLO9": {
        "PI9.1": "Sử dụng được tin học văn phòng, các phần mềm ứng dụng trong quản lý, khai thác tốt thông tin từ Internet đáp ứng yêu cầu trong lĩnh vực chuyên môn",
        "PI9.2": "Giao tiếp được bằng tiếng Anh trong lĩnh vực chuyên môn",
    },
    "PLO12": {
        "PI12.1": "Lập và thực hiện kế hoạch tự học, tự nghiên cứu để nâng cao trình độ chuyên môn, nghiệp vụ",
        "PI12.2": "Triển khai, định hướng, tìm kiếm được cơ hội phát triển nghề nghiệp, thích nghi nhanh với sự thay đổi của môi trường",
        "PI12.3": "Có phẩm chất đạo đức nghề nghiệp, thái độ và tác phong làm việc chuyên nghiệp. Tuân thủ các quy định của pháp luật, chịu trách nhiệm cá nhân trong công việc và xã hội",
        "PI12.4": "Có ý thức, thái độ cầu thị, nghiêm túc, thực hiện đúng các nội quy, quy chế. Từ đó, hình thành tác phong làm việc chuyên nghiệp",
    },
}

# ============================================================
# CNTT — CÔNG NGHỆ THÔNG TIN
# PLO, PI và ma trận HP × PI × IRMA
# Nguồn: KB_PLO_PI_Matrix.md (05/2026)
# ============================================================

CNTT_PLO_DATA: Dict[str, str] = {
    **_SHARED_PLO_DATA,
    "PLO4":  "Người học tốt nghiệp ngành Công nghệ thông tin có khả năng phân tích yêu cầu, thiết kế, hiện thực, kiểm thử và bàn giao phần mềm/ứng dụng số đáp ứng tiêu chí chấp nhận và quản lý thay đổi trong quá trình phát triển",
    "PLO5":  "Người học tốt nghiệp ngành Công nghệ thông tin có khả năng phân rã, thiết kế kiến trúc, tích hợp và bàn giao giải pháp CNTT nhiều thành phần theo chuẩn giao diện dữ liệu, tài liệu hoá và khả năng vận hành",
    "PLO6":  "Người học tốt nghiệp ngành Công nghệ thông tin có khả năng chuẩn bị dữ liệu, xây dựng pipeline và áp dụng các phương pháp AI/phân tích dữ liệu để tạo đầu ra tin cậy, có khả năng giải thích và tái sử dụng cho bài toán thực tế",
    "PLO10": "Người học tốt nghiệp ngành Công nghệ thông tin có khả năng phát triển, tích hợp và kiểm thử ứng dụng trên nền tảng chuyên biệt hoặc hạn chế tài nguyên (mobile/embedded/IoT/robot) đáp ứng ràng buộc thực thi, kết nối và độ ổn định",
    "PLO11": "Người học tốt nghiệp ngành Công nghệ thông tin có khả năng tích hợp, triển khai, vận hành và cải tiến độ tin cậy, an toàn của giải pháp CNTT trên hạ tầng phù hợp thông qua CI/CD, tự động hoá, quan sát hệ thống và xử lý sự cố theo quy trình kỹ thuật",
}

CNTT_PI_DATA: Dict[str, Dict[str, str]] = {
    **_SHARED_PI_DATA,
    "PLO4": {
        "PI4.1": "Phân tích yêu cầu và chuyển thành thiết kế, mã nguồn và bộ kiểm thử có khả năng truy vết theo tiêu chí chấp nhận",
        "PI4.2": "Quản lý thay đổi, sửa lỗi và đóng gói/bàn giao artefact phát hành (mã nguồn, test evidence, tài liệu kỹ thuật, release notes) ở mức phù hợp",
    },
    "PLO5": {
        "PI5.1": "Phân rã hệ thống và mô hình hoá thành phần, luồng xử lý, dữ liệu hoặc giao tiếp giữa các thành phần",
        "PI5.2": "Đặc tả interface/API/dữ liệu và thiết kế giải pháp/kiến trúc ở mức đủ để hiện thực, tích hợp và kiểm thử",
        "PI5.3": "Thực hiện tích hợp và kiểm chứng luồng chạy end-to-end theo kịch bản nghiệp vụ hoặc kỹ thuật",
        "PI5.4": "Đóng gói, tài liệu hoá và bàn giao giải pháp cùng hướng dẫn triển khai/vận hành ở mức phù hợp",
    },
    "PLO6": {
        "PI6.1": "Chuẩn bị, làm sạch, biến đổi và kiểm soát chất lượng dữ liệu phục vụ bài toán",
        "PI6.2": "Xây dựng pipeline dữ liệu/mô hình và đánh giá kết quả bằng metric phù hợp với mục tiêu bài toán",
        "PI6.3": "Diễn giải, trực quan hoá và đóng gói đầu ra mô hình/dữ liệu để hỗ trợ ra quyết định hoặc tích hợp vào hệ thống",
    },
    "PLO10": {
        "PI10.1": "Phát triển và kiểm thử chức năng trên nền tảng chuyên biệt hoặc thiết bị hạn chế tài nguyên, bảo đảm đúng yêu cầu và phù hợp ràng buộc thực thi",
        "PI10.2": "Tích hợp phần mềm với giao tiếp/phần cứng/cảm biến hoặc thành phần nền tảng liên quan; đánh giá độ ổn định, hiệu năng và khả năng vận hành ở mức phù hợp",
    },
    "PLO11": {
        "PI11.1": "Thiết lập pipeline build–test–deploy, đóng gói môi trường chạy và triển khai giải pháp trên hạ tầng/platform phù hợp",
        "PI11.2": "Thiết lập monitoring–logging–alerting; áp dụng kiểm soát an toàn, thực hiện triage/sự cố, thu thập log và RCA ở mức phù hợp",
        "PI11.3": "Thực hiện release/rollback, quản lý thay đổi và đề xuất cải tiến nhằm nâng cao độ sẵn sàng, hiệu năng, độ an toàn và khả năng vận hành",
    },
}

# Ma trận HP × PI × IRMA cho CNTT — nguồn: KB_PLO_PI_Matrix_1.md
CNTT_COURSE_PI_MAP: Dict[str, Dict[str, str]] = _KB_DATA["CNTT"]["course_map"]


# ============================================================
# HTTT — HỆ THỐNG THÔNG TIN
# PLO, PI và ma trận HP × PI × IRMA
# Nguồn: KB_PLO_PI_Matrix.md (05/2026)
# ============================================================

HTTT_PLO_DATA: Dict[str, str] = {
    **_SHARED_PLO_DATA,
    "PLO4":  "Người học tốt nghiệp ngành Hệ thống thông tin có khả năng thu thập, phân tích và đặc tả yêu cầu nghiệp vụ có truy vết, làm cơ sở cho thiết kế, kiểm thử và nghiệm thu HTTT",
    "PLO5":  "Người học tốt nghiệp ngành Hệ thống thông tin có khả năng mô hình hoá quy trình nghiệp vụ và thiết kế giải pháp HTTT theo định hướng dữ liệu–quy trình, bảo đảm phù hợp vận hành tổ chức và ràng buộc kiểm soát",
    "PLO6":  "Người học tốt nghiệp ngành Hệ thống thông tin có khả năng thiết kế mô hình dữ liệu và cơ chế quản trị dữ liệu để bảo đảm chất lượng, nhất quán, quyền sở hữu và khả năng khai thác dữ liệu trong tổ chức",
    "PLO10": "Người học tốt nghiệp ngành Hệ thống thông tin có khả năng xây dựng KPI, dashboard và báo cáo phân tích để hỗ trợ ra quyết định, bảo đảm tính đúng, khả giải thích và phù hợp mục tiêu kinh doanh",
    "PLO11": "Người học tốt nghiệp ngành Hệ thống thông tin có khả năng triển khai, tích hợp, kiểm thử/UAT và bàn giao vận hành HTTT doanh nghiệp theo phương pháp luận phù hợp, bảo đảm quản lý thay đổi, tuân thủ và an toàn thông tin",
}

HTTT_PI_DATA: Dict[str, Dict[str, str]] = {
    **_SHARED_PI_DATA,
    "PLO4": {
        "PI4.1": "Thu thập, phân tích và xác nhận yêu cầu nghiệp vụ; tạo BRD/SRS hoặc user story/use case có tiêu chí chấp nhận và sign-off phù hợp",
        "PI4.2": "Thiết lập và duy trì truy vết yêu cầu–thiết kế–kiểm thử; quản lý thay đổi, ưu tiên, giả định và ràng buộc trong vòng đời yêu cầu",
    },
    "PLO5": {
        "PI5.1": "Mô hình hoá quy trình AS-IS/TO-BE và use case/user flow bằng BPMN/UML để làm rõ bài toán và phạm vi cải tiến",
        "PI5.2": "Thiết kế solution blueprint, luồng xử lý, input/output và cơ chế kiểm soát phù hợp yêu cầu nghiệp vụ và ràng buộc vận hành",
        "PI5.3": "Thiết kế mô hình dữ liệu logic và data dictionary gắn với nghiệp vụ, bảo đảm nhất quán và khả năng tích hợp",
        "PI5.4": "Giải thích và lựa chọn phương án kiến trúc/thiết kế HTTT trên cơ sở trade-off kỹ thuật–nghiệp vụ và khả năng triển khai",
    },
    "PLO6": {
        "PI6.1": "Thiết kế data model, data ownership và data quality rules phục vụ quản trị, khai thác và kiểm soát chất lượng",
        "PI6.2": "Thiết lập data catalog/RACI dữ liệu và cơ chế giám sát chất lượng để bảo đảm tính đúng, nhất quán và khả truy xuất",
        "PI6.3": "Đối sánh dữ liệu nghiệp vụ với mô hình dữ liệu để hỗ trợ tích hợp, báo cáo và ra quyết định trong tổ chức",
    },
    "PLO10": {
        "PI10.1": "Xây dựng KPI tree/định nghĩa KPI và dashboard/báo cáo gắn mục tiêu kinh doanh, có đối soát dữ liệu và khả giải thích",
        "PI10.2": "Phân tích kết quả, diễn giải insight và đề xuất hành động phù hợp cho stakeholder dựa trên bằng chứng dữ liệu",
    },
    "PLO11": {
        "PI11.1": "Thực hiện fit-gap, cấu hình giải pháp và đặc tả tích hợp/mapping dữ liệu cho HTTT doanh nghiệp theo phương pháp luận triển khai phù hợp",
        "PI11.2": "Thiết kế và thực thi SIT/UAT, quản lý lỗi và sử dụng bằng chứng kiểm thử để hỗ trợ quyết định phát hành hoặc cải tiến",
        "PI11.3": "Tổ chức truyền thông, đào tạo, bàn giao vận hành và quản lý thay đổi; áp dụng checklist rủi ro, tuân thủ và an toàn thông tin trong triển khai HTTT",
    },
}

# Ma trận HP × PI × IRMA cho HTTT — nguồn: KB_PLO_PI_Matrix_1.md
HTTT_COURSE_PI_MAP: Dict[str, Dict[str, str]] = _KB_DATA["HTTT"]["course_map"]


# NL3 mapping cho HTTT (cập nhật sang PLO1-12)
HTTT_NL3_PLO_MAP: Dict[str, str] = {
    "NL3-01": "PLO4",   # Khai thác & xác nhận yêu cầu nghiệp vụ
    "NL3-02": "PLO5",   # Mô hình hoá quy trình & truy vết yêu cầu
    "NL3-03": "PLO5",   # Thiết kế giải pháp HTTT theo định hướng dữ liệu
    "NL3-04": "PLO6",   # Xây dựng mô hình dữ liệu & dashboard KPI
    "NL3-05": "PLO11",  # Thực hiện fit-gap & cấu hình ERP/CRM
    "NL3-06": "PLO11",  # Thiết kế & thực thi kiểm thử/UAT
    "NL3-07": "PLO11",  # Tổ chức truyền thông & bàn giao vận hành
    "NL3-08": "PLO12",  # Áp dụng kiểm soát rủi ro, tuân thủ & an toàn thông tin
}

# PO (Program Outcomes) ngành HTTT (giữ nguyên)
HTTT_PO_DATA: Dict[str, str] = {
    "PO1": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò Business/System Analyst, dẫn dắt "
        "phân tích yêu cầu và mô hình hoá quy trình–dữ liệu để tạo BRD/SRS có truy vết cho dự án HTTT "
        "doanh nghiệp, tuân thủ chuẩn mực nghề nghiệp."
    ),
    "PO2": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò tư vấn phân tích–thiết kế giải pháp "
        "HTTT, chuyển hoá nhu cầu vận hành thành kiến trúc, thiết kế dữ liệu và đặc tả I/O hỗ trợ "
        "triển khai–tích hợp, tuân thủ quy định liên quan."
    ),
    "PO3": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò QA/UAT hoặc quản trị chất lượng "
        "HTTT, thiết kế và kiểm soát kiểm thử–nghiệm thu kèm bằng chứng, bảo đảm an toàn, bảo mật–riêng "
        "tư dữ liệu và tuân thủ quy định."
    ),
    "PO4": (
        "Sau 3–5 năm tốt nghiệp, người học có thể đảm nhiệm vai trò chuyên viên triển khai/CSKH HTTT, "
        "phối hợp stakeholder đa bên để tư vấn, đào tạo người dùng và quản trị thay đổi, đảm bảo "
        "bàn giao–vận hành theo SLA trong bối cảnh dự án/sản phẩm."
    ),
    "PO5": (
        "Người học phát triển năng lực tự học suốt đời và chuẩn hoá tri thức nghiệp vụ–dữ liệu để "
        "tạo giá trị cải tiến liên tục; có khả năng đổi mới qua portfolio/case study và thích ứng "
        "chuyển đổi số/AI nhằm nâng cao hiệu quả nghề nghiệp."
    ),
}


# ============================================================
# KHMT — KHOA HỌC MÁY TÍNH
# PLO, PI và ma trận HP × PI × IRMA
# Nguồn: KB_PLO_PI_Matrix.md (05/2026)
# ============================================================

KHMT_PLO_DATA: Dict[str, str] = {
    **_SHARED_PLO_DATA,
    "PLO4":  "Người học tốt nghiệp ngành Khoa học máy tính có khả năng mô hình hoá bài toán, phân tích, lựa chọn và thiết kế thuật toán/mô hình phù hợp, đồng thời kiểm chứng độ đúng và hiệu quả bằng kiểm thử, benchmark hoặc phân tích thực nghiệm",
    "PLO5":  "Người học tốt nghiệp ngành Khoa học máy tính có khả năng xây dựng pipeline dữ liệu và phát triển, huấn luyện, đánh giá mô hình học máy, học sâu để khai thác, xử lý, phân tích dữ liệu và tạo ra kết quả cho bài toán thực tế",
    "PLO6":  "Người học tốt nghiệp ngành Khoa học máy tính có khả năng thiết kế và thực hiện thí nghiệm, ghi nhận và tái lập kết quả để so sánh mô hình, giải pháp về dữ liệu, AI một cách có hệ thống",
    "PLO10": "Người học tốt nghiệp ngành Khoa học máy tính có khả năng áp dụng nguyên lý hệ thống (mạng, hệ điều hành, cơ sở dữ liệu, an toàn) để thiết kế và đánh giá kiến trúc, luồng xử lý và môi trường thực thi cho bài toán về dữ liệu, AI",
    "PLO11": "Người học tốt nghiệp ngành Khoa học máy tính có khả năng thực hiện hoạt động học thuật và nghề nghiệp KHMT một cách có trách nhiệm; tuân thủ pháp luật, liêm chính nghiên cứu, đánh giá rủi ro đạo đức của dữ liệu/mô hình/giải pháp và chủ động thích ứng, cải tiến công nghệ trong bối cảnh nghề nghiệp",
}

KHMT_PI_DATA: Dict[str, Dict[str, str]] = {
    **_SHARED_PI_DATA,
    "PLO4": {
        "PI4.1": "Đặc tả bài toán (I/O, ràng buộc, tiêu chí) và biện minh việc lựa chọn mô hình/thuật toán trên cơ sở giả định, dữ liệu và nền tảng toán học/khoa học tính toán",
        "PI4.2": "Kiểm chứng độ đúng, độ phức tạp hoặc hiệu quả của mô hình/thuật toán bằng test suite, benchmark hoặc phân tích",
    },
    "PLO5": {
        "PI5.1": "Thu thập, trích xuất, làm sạch và chuẩn hoá dữ liệu theo tiêu chí chất lượng dữ liệu",
        "PI5.2": "Xây dựng pipeline xử lý dữ liệu và huấn luyện mô hình phù hợp với mục tiêu bài toán",
        "PI5.3": "Đánh giá mô hình bằng metric phù hợp; trực quan hoá và diễn giải kết quả",
        "PI5.4": "Chuyển đầu ra mô hình thành kết quả/báo cáo có khả năng sử dụng cho bài toán thực tế",
    },
    "PLO6": {
        "PI6.1": "Xây dựng protocol thí nghiệm (dataset split, baseline, metric, môi trường) cho bài toán dữ liệu/AI",
        "PI6.2": "Ghi log, quản lý cấu hình môi trường và tái lập kết quả thí nghiệm một cách nhất quán",
        "PI6.3": "Thực hiện ablation, benchmark hoặc so sánh tham số để rút ra kết luận có căn cứ",
    },
    "PLO10": {
        "PI10.1": "Thiết kế dữ liệu, luồng xử lý, kiến trúc và môi trường thực thi cho giải pháp dữ liệu/AI phù hợp ràng buộc",
        "PI10.2": "Đánh giá và đề xuất kiểm soát về hiệu năng, độ tin cậy, an toàn dữ liệu và quyền riêng tư ở mức phù hợp",
    },
    "PLO11": {
        "PI11.1": "Áp dụng trích dẫn/giấy phép dữ liệu–mã nguồn, liêm chính nghiên cứu và các yêu cầu pháp lý trong phát triển, đánh giá giải pháp",
        "PI11.2": "Nhận diện, phân tích và đề xuất biện pháp giảm thiểu rủi ro đạo đức của dữ liệu/mô hình/hệ thống (riêng tư, thiên lệch, an toàn)",
        "PI11.3": "Lập kế hoạch tự học/tự nghiên cứu, cập nhật công nghệ và đề xuất hướng cải tiến/ứng dụng có tính khả thi trong bối cảnh nghề nghiệp KHMT",
    },
}

# Ma trận HP × PI × IRMA cho KHMT — nguồn: KB_PLO_PI_Matrix_1.md
KHMT_COURSE_PI_MAP: Dict[str, Dict[str, str]] = _KB_DATA["KHMT"]["course_map"]


# NL3 mapping cho KHMT (cập nhật sang PLO1-12)
KHMT_NL3_PLO_MAP: Dict[str, str] = {
    "NL3-01": "PLO5",   # Thu thập–trích xuất–chuẩn hoá dữ liệu
    "NL3-02": "PLO6",   # Thiết kế và thực hiện thí nghiệm AI
    "NL3-03": "PLO5",   # Pipeline dữ liệu & mô hình AI/ML
    "NL3-04": "PLO10",  # Kiến trúc & hệ thống AI
    "NL3-05": "PLO10",  # Triển khai và môi trường thực thi
    "NL3-06": "PLO11",  # Đạo đức AI & tuân thủ
    "NL3-07": "PLO4",   # Mô hình hoá & phân tích thuật toán
    "NL3-08": "PLO11",  # Nghiên cứu học thuật
}


# ============================================================
# PROGRAM REGISTRY - Danh mục các chương trình đào tạo
# ============================================================

PROGRAM_DATA: Dict[str, dict] = {
    "GENERIC": {
        "name": "Chương trình chung (Khoa CNTT)",
        "code": "GENERIC",
        "plo": PLO_DATA,
        "pi": PI_DATA,
        "nl3_plo_map": {},
        "po": {},
        "docs_path": None,
        "course_pi_map": {},
    },
    "CNTT": {
        "name": "Công nghệ thông tin",
        "code": "CNTT",
        "plo": CNTT_PLO_DATA,
        "pi": CNTT_PI_DATA,
        "nl3_plo_map": {},
        "po": {},
        "docs_path": "TailieuMD/CNTT",
        "course_pi_map": CNTT_COURSE_PI_MAP,
    },
    "HTTT": {
        "name": "Hệ thống thông tin",
        "code": "HTTT",
        "plo": HTTT_PLO_DATA,
        "pi": HTTT_PI_DATA,
        "nl3_plo_map": HTTT_NL3_PLO_MAP,
        "po": HTTT_PO_DATA,
        "docs_path": "TailieuMD/HTTT",
        "course_pi_map": HTTT_COURSE_PI_MAP,
    },
    "KHMT": {
        "name": "Khoa học máy tính",
        "code": "KHMT",
        "plo": KHMT_PLO_DATA,
        "pi": KHMT_PI_DATA,
        "nl3_plo_map": KHMT_NL3_PLO_MAP,
        "po": {},
        "docs_path": "TailieuMD/KHMT",
        "course_pi_map": KHMT_COURSE_PI_MAP,
    },
}

# Combined lookup (tất cả chương trình)
ALL_PLO_DATA: Dict[str, str] = {**PLO_DATA, **CNTT_PLO_DATA, **HTTT_PLO_DATA, **KHMT_PLO_DATA}
ALL_PI_DATA: Dict[str, Dict[str, str]] = {**PI_DATA, **CNTT_PI_DATA, **HTTT_PI_DATA, **KHMT_PI_DATA}


# ============================================================
# EXTENDED HELPER FUNCTIONS (multi-program aware)
# ============================================================

def get_program_plo_data(program: str) -> Dict[str, str]:
    """Lấy PLO_DATA cho chương trình cụ thể."""
    return PROGRAM_DATA.get(program, PROGRAM_DATA["GENERIC"])["plo"]


def get_program_pi_data(program: str) -> Dict[str, Dict[str, str]]:
    """Lấy PI_DATA cho chương trình cụ thể."""
    return PROGRAM_DATA.get(program, PROGRAM_DATA["GENERIC"])["pi"]


def get_program_list() -> List[str]:
    """Trả về danh sách mã chương trình đào tạo."""
    return list(PROGRAM_DATA.keys())


def get_pi_description_extended(pi_code: str) -> str:
    """Lấy mô tả PI từ tất cả chương trình."""
    for plo, pis in ALL_PI_DATA.items():
        if pi_code in pis:
            return pis[pi_code]
    return ""


def get_plo_for_pi_extended(pi_code: str) -> str:
    """Xác định PLO chứa PI này từ tất cả chương trình."""
    for plo, pis in ALL_PI_DATA.items():
        if pi_code in pis:
            return plo
    return ""


def get_pi_list_text_for_program(program: str = "GENERIC") -> str:
    """Trả về danh sách PI dạng text cho chương trình cụ thể."""
    plo_data = get_program_plo_data(program)
    pi_data = get_program_pi_data(program)
    lines = []
    for plo_code, pis in pi_data.items():
        plo_desc = plo_data.get(plo_code, "")
        lines.append(f"\n{plo_code}: {plo_desc}")
        for pi_code, pi_desc in pis.items():
            lines.append(f"  {pi_code}: {pi_desc}")
    return "\n".join(lines)


def get_plo_list_text_for_program(program: str = "GENERIC") -> str:
    """Trả về danh sách PLO dạng text cho chương trình cụ thể."""
    plo_data = get_program_plo_data(program)
    lines = [f"{code}: {desc}" for code, desc in plo_data.items()]
    return "\n".join(lines)


def detect_program_from_plo(plo_code: str) -> str:
    """Xác định chương trình từ mã PLO."""
    if plo_code.startswith("PLO-IS"):  # legacy
        return "HTTT"
    if plo_code.startswith("PLO-CS"):  # legacy
        return "KHMT"
    # PLO1-12 is shared across programs — cannot determine program from PLO code alone
    return "GENERIC"


# ============================================================
# IRMA helpers (multi-program)
# ============================================================

def get_irma_for_course_pi(course_code: str, pi_code: str, program: str = "KHMT") -> Optional[str]:
    """Tra cứu mức IRMA của một PI trong học phần, theo ngành."""
    _p = (program or "KHMT").upper()
    maps = {
        "CNTT": CNTT_COURSE_PI_MAP,
        "HTTT": HTTT_COURSE_PI_MAP,
        "KHMT": KHMT_COURSE_PI_MAP,
    }
    return maps.get(_p, KHMT_COURSE_PI_MAP).get(course_code, {}).get(pi_code)


# Keyword fallback patterns for courses not in the official matrix
_KEYWORD_PI_FALLBACK: Dict[str, List] = {
    "KHMT": [
        (r"NLP|ngôn ngữ|language model|NLU|NLG", ["PI5.2", "PI5.3"]),
        (r"học máy|machine learning|deep learning|học sâu", ["PI5.2", "PI5.3", "PI6.1"]),
        (r"dữ liệu lớn|big data|khai phá", ["PI5.1", "PI5.2", "PI10.1"]),
        (r"kiến trúc|deploy|vận hành|devops|mlops", ["PI10.1", "PI10.2", "PI11.1"]),
        (r"đạo đức|ethics|an toàn AI|responsible", ["PI11.1", "PI11.2"]),
        (r"thị giác|computer vision|image", ["PI5.2", "PI5.3", "PI6.3"]),
        (r"đồ án|dự án|project|capstone", ["PI4.1", "PI4.2", "PI5.1", "PI5.2"]),
        (r"thực tập|internship", ["PI7.1", "PI7.2", "PI8.1", "PI8.2"]),
    ],
    "HTTT": [
        (r"phân tích nghiệp vụ|BA|requirements|yêu cầu", ["PI4.1", "PI4.2"]),
        (r"HTTT quản lý|ERP|BI|dashboard|KPI", ["PI5.2", "PI6.3", "PI10.1"]),
        (r"kiểm thử|UAT|testing|SIT", ["PI11.2"]),
        (r"triển khai|deployment|tích hợp|integration", ["PI11.1", "PI11.3"]),
        (r"đồ án|dự án|project|capstone", ["PI4.1", "PI4.2", "PI5.1", "PI5.2"]),
        (r"thực tập|internship", ["PI7.1", "PI7.2", "PI8.1", "PI8.2"]),
    ],
    "CNTT": [
        (r"NLP|ngôn ngữ|language model", ["PI6.2", "PI6.3"]),
        (r"học máy|machine learning|AI|deep learning", ["PI6.1", "PI6.2", "PI6.3"]),
        (r"kiến trúc|architect|thiết kế hệ thống", ["PI5.1", "PI5.2"]),
        (r"kiểm thử|testing|QA|test", ["PI4.1", "PI4.2"]),
        (r"deploy|devops|vận hành|CI/CD", ["PI11.1", "PI11.2", "PI11.3"]),
        (r"mobile|IoT|nhúng|embedded", ["PI10.1", "PI10.2"]),
        (r"đồ án|dự án|project|capstone", ["PI4.1", "PI4.2", "PI5.3", "PI5.4"]),
        (r"thực tập|internship", ["PI7.1", "PI7.2", "PI8.1", "PI8.2"]),
    ],
}


def _keyword_fallback_pi_context(course_code: str, program: str, course_name: str = "") -> str:
    """Keyword-based fallback PI context for courses not in the official matrix."""
    import re
    patterns = _KEYWORD_PI_FALLBACK.get(program, [])
    search_text = (course_code + " " + course_name).lower()
    matched_pis: List[str] = []
    for pattern, pis in patterns:
        if re.search(pattern, search_text, re.IGNORECASE):
            matched_pis.extend(pis)
    matched_pis = list(dict.fromkeys(matched_pis))  # dedup, preserve order
    if not matched_pis:
        return ""
    pi_data_map = {"CNTT": CNTT_PI_DATA, "HTTT": HTTT_PI_DATA, "KHMT": KHMT_PI_DATA}
    pi_data = pi_data_map.get(program, KHMT_PI_DATA)
    lines = [f"=== GỢI Ý PI CHO HỌC PHẦN {course_code} (KEYWORD MATCHING — CHƯA CÓ TRONG MA TRẬN) ==="]
    for pi_code in matched_pis:
        for plo_code, pis in pi_data.items():
            if pi_code in pis:
                lines.append(f"  {pi_code} (thuộc {plo_code}): {pis[pi_code]}")
                break
    lines.append("LƯU Ý: Đây là gợi ý tự động từ tên HP. GV cần xác nhận ánh xạ chính xác.")
    return "\n".join(lines)


def get_pi_context_for_course(course_code: str, program: str = "KHMT", course_name: str = "") -> str:
    """Multi-program: trả về PI/IRMA context cho một học phần từ ma trận chính thức."""
    _p = (program or "KHMT").upper()
    course_map_lookup = {
        "CNTT": CNTT_COURSE_PI_MAP,
        "HTTT": HTTT_COURSE_PI_MAP,
        "KHMT": KHMT_COURSE_PI_MAP,
    }
    pi_data_lookup = {
        "CNTT": CNTT_PI_DATA,
        "HTTT": HTTT_PI_DATA,
        "KHMT": KHMT_PI_DATA,
    }
    course_map = course_map_lookup.get(_p, KHMT_COURSE_PI_MAP).get(course_code, {})
    if not course_map:
        return _keyword_fallback_pi_context(course_code, _p, course_name)
    pi_data = pi_data_lookup.get(_p, KHMT_PI_DATA)
    lines = [f"=== IRMA CỦA HỌC PHẦN {course_code} THEO MA TRẬN NGÀNH {_p} ==="]
    for pi_code, irma in course_map.items():
        pi_desc = ""
        plo = ""
        for plo_code, pis in pi_data.items():
            if pi_code in pis:
                pi_desc = pis[pi_code]
                plo = plo_code
                break
        lines.append(f"  {pi_code} (thuộc {plo}) [{irma}]: {pi_desc}")
    lines.append("QUAN TRỌNG: Các PI và mức IRMA trên là căn cứ chính thức từ ma trận ngành. Ưu tiên ánh xạ CLO vào các PI này với mức IRMA tương ứng.")
    return "\n".join(lines)


def get_plo_for_pi(pi_code: str, nganh: str = None) -> str:
    """Xác định PLO chứa PI này. nganh='CNTT'|'HTTT'|'KHMT' để tra đúng ngành."""
    if nganh:
        pi_data_map = {"CNTT": CNTT_PI_DATA, "HTTT": HTTT_PI_DATA, "KHMT": KHMT_PI_DATA}
        pi_data = pi_data_map.get(nganh.upper(), PI_DATA)
    else:
        pi_data = PI_DATA
    for plo, pis in pi_data.items():
        if pi_code in pis:
            return plo
    return ""
