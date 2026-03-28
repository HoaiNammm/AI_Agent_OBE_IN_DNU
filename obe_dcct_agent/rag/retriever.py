"""
retriever.py - RAG query functions.

Provides a clean ``retrieve_context`` function that can be called by any agent.
"""

from __future__ import annotations

import logging

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
)

logger = logging.getLogger(__name__)

_vector_store: QdrantVectorStore | None = None


def _get_vector_store() -> QdrantVectorStore:
    """Lazily initialise and return the Qdrant vector store."""
    global _vector_store
    if _vector_store is None:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)
        embeddings = OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            model=EMBEDDING_MODEL,
        )
        _vector_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION,
            embedding=embeddings,
        )
    return _vector_store


def retrieve_context(query: str, k: int = 4) -> str:
    """
    Retrieve the top-*k* most relevant document chunks for *query*.

    Args:
        query: Natural language query string.
        k: Number of chunks to retrieve.

    Returns:
        Concatenated context string (empty string on failure).
    """
    try:
        store = _get_vector_store()
        docs = store.similarity_search(query, k=k)
        context = "\n\n".join(d.page_content for d in docs)
        logger.info("[Retriever] Retrieved %d chunks for query: %.60s…", len(docs), query)
        return context
    except Exception as exc:
        logger.warning("[Retriever] Failed to retrieve context: %s", exc)
        return ""
