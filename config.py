# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

for directory in [OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Models
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
)
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

AGENT_MODELS = {
    "supervisor": CLAUDE_MODEL if ANTHROPIC_API_KEY else GEMINI_MODEL,
    "understand": GEMINI_MODEL,
    "mapping": CLAUDE_MODEL if ANTHROPIC_API_KEY else GEMINI_MODEL,
    "teaching_plan": GEMINI_MODEL,
    "assessment": CLAUDE_MODEL if ANTHROPIC_API_KEY else GEMINI_MODEL,
    "validator": CLAUDE_MODEL if ANTHROPIC_API_KEY else GEMINI_MODEL,
    "critic": CLAUDE_MODEL if ANTHROPIC_API_KEY else GEMINI_MODEL,
}

MODEL_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 4096,
}

CONFIDENCE_THRESHOLDS = {
    "high": 90,
    "medium": 70,
    "low": 50,
}

def get_agent_model(agent_name: str) -> str:
    return AGENT_MODELS.get(agent_name, GEMINI_MODEL)

def validate_config() -> bool:
    if not GOOGLE_API_KEY and not ANTHROPIC_API_KEY:
        print(" Cần ít nhất một API Key: GOOGLE_API_KEY hoặc ANTHROPIC_API_KEY")
        return False
    print(" Configuration validated successfully!")
    return True
