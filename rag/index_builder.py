"""
RAG Index Builder — Lớp RAG (Layer 2)

CHỈ index nội dung prose/examples vào Qdrant.
KHÔNG index PLO/PI rules, IRMA rules, Bloom taxonomy, assessment rules.

Lý do tách 2 lớp:
  • Layer 1 (Hardcode) — utils/kb.py: PLO/PI data, IRMA, assessment, forbidden verbs.
    Agent gọi trực tiếp bằng function call. Đảm bảo determinism tuyệt đối.
  • Layer 2 (RAG) — rag/: DCCT examples, TailieuMD prose, domain context.
    Qdrant retriever chỉ gọi khi agent cần ngữ cảnh bổ sung, không dùng để tra rule.

Nếu PI rules ở RAG: cosine similarity có thể miss rule cần thiết
→ agent mapping ra PI sai mà không có gì catch lại.
"""

import os
from utils.logger import get_logger

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
    """
    Xây dựng danh sách Document CHỈ gồm nội dung prose/examples.

    KHÔNG bao gồm:
      - PLO/PI data       → dùng utils/kb.get_pi_list_for_prompt()
      - IRMA rules        → dùng utils/kb.get_irma_for_prompt()
      - Bloom taxonomy    → dùng utils/obe_utils.BLOOM_VERBS
      - Assessment rules  → dùng utils/kb.get_assessment_for_prompt()

    Chỉ bao gồm:
      - TailieuMD Markdown (prose mô tả ngành KHMT/HTTT)
      - (Tương lai) DCCT examples đã được chuyên gia review
    """
    docs = []
    docs.extend(_load_tailieu_md_documents())
    return docs


def _load_tailieu_md_documents() -> list:
    """
    Nạp các tài liệu Markdown thực tế từ thư mục TailieuMD.
    Hỗ trợ HTTT và KHMT, bỏ qua file lỗi mã hóa.
    """
    from langchain_core.documents import Document

    docs = []

    # Tìm thư mục TailieuMD từ workspace root
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tailieu_base = os.path.join(os.path.dirname(workspace_root), "TailieuMD")

    # Fallback: tìm bên trong cùng thư mục workspace
    if not os.path.isdir(tailieu_base):
        tailieu_base = os.path.join(workspace_root, "..", "TailieuMD")
    if not os.path.isdir(tailieu_base):
        logger.warning(f"Không tìm thấy thư mục TailieuMD tại: {tailieu_base}")
        return docs

    program_dirs = {
        "HTTT": os.path.join(tailieu_base, "HTTT"),
        "KHMT": os.path.join(tailieu_base, "KHMT"),
    }

    for program_code, dir_path in program_dirs.items():
        if not os.path.isdir(dir_path):
            logger.warning(f"Không tìm thấy thư mục {program_code}: {dir_path}")
            continue

        md_files = [f for f in os.listdir(dir_path) if f.endswith(".md")]
        loaded = 0
        for fname in md_files:
            fpath = os.path.join(dir_path, fname)
            try:
                with open(fpath, encoding="utf-8") as fp:
                    content = fp.read().strip()
                if not content:
                    continue
                # Giới hạn 4000 ký tự / chunk để tránh quá tải embedding
                chunks = [content[i : i + 4000] for i in range(0, len(content), 4000)]
                for idx, chunk in enumerate(chunks):
                    docs.append(
                        Document(
                            page_content=f"[{program_code}][{fname}] {chunk}",
                            metadata={
                                "type": "tailieu_md",
                                "program": program_code,
                                "filename": fname,
                                "chunk_index": idx,
                            },
                        )
                    )
                loaded += 1
            except Exception as e:
                logger.warning(f"Bỏ qua file {fname}: {e}")

        logger.info(f"Đã nạp {loaded}/{len(md_files)} tài liệu Markdown cho {program_code}")

    return docs


async def _create_vector_store(docs: list):
    """Tạo Qdrant in-memory vector store."""
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    from config import GOOGLE_API_KEY

    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
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
