"""
frontend/utils.py - Utility functions for the Streamlit frontend.
"""

from __future__ import annotations

import os


def get_download_bytes(file_path: str) -> bytes:
    """Read a file and return its bytes for Streamlit download_button."""
    with open(file_path, "rb") as f:
        return f.read()


def format_file_size(path: str) -> str:
    """Return human-readable file size string."""
    size_bytes = os.path.getsize(path)
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
