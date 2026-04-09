"""
RAG Index Builder - Khởi tạo vector store với kiến thức OBE
Sử dụng Qdrant in-memory để dễ triển khai, không cần server riêng
"""

import json
from typing import Optional
from utils.logger import get_logger
from utils.obe_utils import PLO_DATA, PI_DATA, BLOOM_LEVELS, IRMA_LEVELS

logger = get_logger("rag.index_builder")

# Global vector store instance
_vector_store = None
_retriever = None


EMBEDDING_DIMENSION = 768  # Gemini embedding-001 output dimension


async def initialize_rag(force_rebuild: bool = False) -> bool:
    """
    Khởi tạo RAG system với dữ liệu OBE.
    
    Args:
        force_rebuild: Rebuild index dù đã tồn tại
    
    Returns:
        True nếu thành công
    """
    global _vector_store, _retriever

    if _vector_store is not None and not force_rebuild:
        logger.info("RAG đã được khởi tạo, bỏ qua.")
        return True

    logger.info("Đang khởi tạo RAG system...")

    try:
        docs = _build_obe_documents()
        _vector_store = await _create_vector_store(docs)
        _retriever = _vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )
        logger.info(f"RAG khởi tạo thành công với {len(docs)} tài liệu OBE")
        return True

    except Exception as e:
        logger.warning(f"Không thể khởi tạo Qdrant vector store: {e}")
        logger.info("Sử dụng fallback: kiến thức OBE từ obe_utils trực tiếp")
        _vector_store = None
        _retriever = None
        return False


def _build_obe_documents() -> list:
    """Xây dựng danh sách Document từ dữ liệu OBE."""
    from langchain_core.documents import Document

    docs = []

    # PLO documents
    for plo_code, plo_desc in PLO_DATA.items():
        docs.append(
            Document(
                page_content=f"{plo_code}: {plo_desc}",
                metadata={"type": "plo", "code": plo_code},
            )
        )

    # PI documents (kèm PLO cha)
    for plo_code, pis in PI_DATA.items():
        for pi_code, pi_desc in pis.items():
            docs.append(
                Document(
                    page_content=f"{pi_code} (thuộc {plo_code}): {pi_desc}",
                    metadata={
                        "type": "pi",
                        "code": pi_code,
                        "parent_plo": plo_code,
                    },
                )
            )

    # Bloom taxonomy documents
    bloom_text = "\n".join(
        [f"Mức {lvl} - {name}: Các động từ hành động tiêu biểu"
         for lvl, name in BLOOM_LEVELS.items()]
    )
    docs.append(
        Document(
            page_content=f"Bloom Taxonomy - Thang đánh giá nhận thức:\n{bloom_text}",
            metadata={"type": "bloom"},
        )
    )

    # IRMA levels document
    irma_text = "\n".join(
        [f"{level}: {desc}" for level, desc in IRMA_LEVELS.items()]
    )
    docs.append(
        Document(
            page_content=f"Mức độ IRMA trong OBE:\n{irma_text}",
            metadata={"type": "irma"},
        )
    )

    # OBE principles document
    docs.append(
        Document(
            page_content="""Nguyên tắc OBE (Outcome-Based Education):
1. CLO phải SMART: Specific, Measurable, Achievable, Relevant, Time-bound
2. Constructive Alignment: CLO → Teaching Activities → Assessment phải nhất quán
3. Assessment as Learning: đánh giá là công cụ học tập, không chỉ kiểm tra
4. Continuous Improvement: DCCT được cải tiến liên tục qua phản hồi
5. Student-Centered: thiết kế từ chuẩn đầu ra của sinh viên""",
            metadata={"type": "obe_principles"},
        )
    )

    return docs


async def _create_vector_store(docs: list):
    """Tạo Qdrant in-memory vector store."""
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    from config import GOOGLE_API_KEY, GEMINI_EMBEDDING_MODEL

    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBEDDING_MODEL,
            google_api_key=GOOGLE_API_KEY,
        )
    except Exception:
        # Fallback: dùng fake embeddings nếu không có API
        from langchain_core.embeddings import FakeEmbeddings
        embeddings = FakeEmbeddings(size=768)

    # Tạo Qdrant in-memory client
    client = QdrantClient(":memory:")
    collection_name = "obe_knowledge"

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE),
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    vector_store.add_documents(docs)
    return vector_store


def get_retriever():
    """Lấy retriever đã khởi tạo."""
    return _retriever


def is_initialized() -> bool:
    """Kiểm tra RAG đã được khởi tạo chưa."""
    return _vector_store is not None
