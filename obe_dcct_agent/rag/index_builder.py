"""
index_builder.py - Qdrant + Embedding + Ingest data.

Use this script to build or rebuild the RAG knowledge base from
OBE guidelines, DNU programme specifications, and sample DCCTs.

Usage:
    python -m rag.index_builder --source docs/obe_guidelines.md
    python -m rag.index_builder --source path/to/folder
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
)
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def get_qdrant_client() -> QdrantClient:
    """Return a configured Qdrant client."""
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None)


def ensure_collection(client: QdrantClient, vector_size: int = 1536) -> None:
    """Create the Qdrant collection if it doesn't already exist."""
    existing = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection: %s", QDRANT_COLLECTION)
    else:
        logger.info("Qdrant collection already exists: %s", QDRANT_COLLECTION)


def load_documents(source: str):
    """Load documents from a file or directory."""
    source_path = Path(source)
    if source_path.is_dir():
        loader = DirectoryLoader(
            str(source_path),
            glob="**/*.{txt,md,docx}",
            loader_cls=TextLoader,
            silent_errors=True,
        )
    elif source_path.suffix == ".docx":
        loader = UnstructuredWordDocumentLoader(str(source_path))
    else:
        loader = TextLoader(str(source_path), encoding="utf-8")
    return loader.load()


def build_index(source: str) -> None:
    """Ingest documents from *source* into the Qdrant vector store."""
    logger.info("Loading documents from: %s", source)
    docs = load_documents(source)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)
    logger.info("Split into %d chunks.", len(chunks))

    embeddings = OpenAIEmbeddings(
        api_key=OPENAI_API_KEY,
        model=EMBEDDING_MODEL,
    )

    client = get_qdrant_client()
    ensure_collection(client)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )
    vector_store.add_documents(chunks)
    logger.info("Indexed %d chunks into '%s'.", len(chunks), QDRANT_COLLECTION)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Build RAG index for OBE DCCT Agent")
    parser.add_argument("--source", required=True, help="Path to file or folder to ingest")
    args = parser.parse_args()
    build_index(args.source)


if __name__ == "__main__":
    main()
