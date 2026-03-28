"""
config.py - Configuration for API keys, models, and thresholds.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

# ── Embeddings ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ── Qdrant ─────────────────────────────────────────────────────────────────────
QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "obe_dcct")

# ── OBE Thresholds ─────────────────────────────────────────────────────────────
MIN_CLO_COUNT: int = int(os.getenv("MIN_CLO_COUNT", "3"))
MAX_CLO_COUNT: int = int(os.getenv("MAX_CLO_COUNT", "8"))
MIN_CONFIDENCE_SCORE: float = float(os.getenv("MIN_CONFIDENCE_SCORE", "0.75"))

# ── IRMA Weights (Instruction, Research, Mentoring, Assessment) ────────────────
IRMA_WEIGHTS: dict = {
    "I": float(os.getenv("IRMA_WEIGHT_I", "0.40")),
    "R": float(os.getenv("IRMA_WEIGHT_R", "0.25")),
    "M": float(os.getenv("IRMA_WEIGHT_M", "0.15")),
    "A": float(os.getenv("IRMA_WEIGHT_A", "0.20")),
}

# ── Credit / Hour Mapping ──────────────────────────────────────────────────────
CREDIT_HOURS_MAP: dict = {
    1: {"lecture": 15, "practice": 0, "self_study": 30},
    2: {"lecture": 30, "practice": 0, "self_study": 60},
    3: {"lecture": 30, "practice": 15, "self_study": 90},
    4: {"lecture": 45, "practice": 15, "self_study": 120},
}

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: str = os.path.join(os.path.dirname(__file__), "logs")

# ── Output ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR: str = os.path.join(os.path.dirname(__file__), "output")
TEMPLATE_PATH: str = os.path.join(
    os.path.dirname(__file__), "templates", "DCCT_Template.docx"
)
