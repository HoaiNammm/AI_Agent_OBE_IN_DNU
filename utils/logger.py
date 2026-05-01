"""
Logger - Hệ thống ghi log có cấu trúc cho OBE DCCT Agent
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGING = True
except ImportError:
    JSON_LOGGING = False

# Thư mục logs
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    Tạo logger có cấu trúc với tên module cụ thể.
    
    Args:
        name: Tên module (vd: "agents.supervisor")
    
    Returns:
        Logger instance đã được cấu hình
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Console handler - INFO level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    if JSON_LOGGING:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler - DEBUG level
    log_filename = LOGS_DIR / f"dcct_agent_{datetime.now().strftime('%Y%m%d')}.log"
    try:
        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass  # Bỏ qua nếu không ghi được file log

    return logger


# Các logger mặc định theo module
agent_logger = get_logger("agents")
tool_logger = get_logger("tools")
rag_logger = get_logger("rag")
export_logger = get_logger("export")
