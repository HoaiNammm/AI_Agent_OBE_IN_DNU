"""
RAG Retriever - Truy xuất thông tin OBE từ vector store
Fallback về dữ liệu tĩnh nếu RAG chưa được khởi tạo
"""

from typing import List, Optional
from utils.logger import get_logger
from utils.obe_utils import (
    PLO_DATA, PI_DATA, get_pi_list_text, get_plo_list_text,
    get_pi_description, get_plo_for_pi
)

logger = get_logger("rag.retriever")


def retrieve_relevant_plos(query: str, k: int = 5) -> List[str]:
    """
    Truy xuất PLO liên quan đến query.
    
    Args:
        query: Câu hỏi/mô tả để tìm PLO phù hợp
        k: Số kết quả trả về
    
    Returns:
        Danh sách mô tả PLO liên quan
    """
    from rag.index_builder import get_retriever

    retriever = get_retriever()

    if retriever is not None:
        try:
            docs = retriever.invoke(query)
            plo_docs = [d for d in docs if d.metadata.get("type") == "plo"]
            return [d.page_content for d in plo_docs[:k]]
        except Exception as e:
            logger.warning(f"Lỗi RAG retrieval: {e}, dùng fallback")

    # Fallback: trả về tất cả PLO
    return [f"{code}: {desc}" for code, desc in list(PLO_DATA.items())[:k]]


def retrieve_relevant_pis(query: str, k: int = 8) -> List[str]:
    """
    Truy xuất PI liên quan đến query.
    
    Args:
        query: Mô tả CLO/nội dung để tìm PI phù hợp
        k: Số kết quả trả về
    
    Returns:
        Danh sách mô tả PI liên quan
    """
    from rag.index_builder import get_retriever

    retriever = get_retriever()

    if retriever is not None:
        try:
            docs = retriever.invoke(query)
            pi_docs = [d for d in docs if d.metadata.get("type") == "pi"]
            return [d.page_content for d in pi_docs[:k]]
        except Exception as e:
            logger.warning(f"Lỗi RAG retrieval: {e}, dùng fallback")

    # Fallback: trả về PI từ các PLO phổ biến
    results = []
    for plo_code, pis in list(PI_DATA.items())[:4]:
        for pi_code, pi_desc in pis.items():
            results.append(f"{pi_code} (thuộc {plo_code}): {pi_desc}")
    return results[:k]


def get_full_obe_context() -> str:
    """
    Lấy toàn bộ context OBE để đưa vào prompt.
    Sử dụng khi cần toàn bộ dữ liệu PLO/PI.
    """
    return f"""=== CHUẨN ĐẦU RA CHƯƠNG TRÌNH (PLO) ===
{get_plo_list_text()}

=== CHỈ SỐ NĂNG LỰC (PI) ===
{get_pi_list_text()}"""


def get_plo_pi_context_for_course(course_name: str, clo_descriptions: List[str]) -> str:
    """
    Lấy context PLO/PI phù hợp nhất cho học phần và CLO.
    
    Args:
        course_name: Tên học phần
        clo_descriptions: Danh sách mô tả CLO
    
    Returns:
        Text context với PLO/PI liên quan
    """
    # Kết hợp course name và CLO descriptions để tìm context
    combined_query = f"{course_name} " + " ".join(clo_descriptions[:3])

    relevant_pis = retrieve_relevant_pis(combined_query, k=10)

    if not relevant_pis:
        return get_full_obe_context()

    return f"""=== DANH SÁCH PLO (Chuẩn đầu ra chương trình) ===
{get_plo_list_text()}

=== PI LIÊN QUAN NHẤT ===
""" + "\n".join(relevant_pis)
