"""
helpers.py - Common utility functions used across the project.
"""

from __future__ import annotations

from typing import Any, Iterable, TypeVar

T = TypeVar("T")


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp *value* to the range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def flatten(nested: Iterable[Iterable[T]]) -> list[T]:
    """Flatten one level of nesting from a list of lists."""
    return [item for sublist in nested for item in sublist]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide numerator by denominator, returning *default* if denominator is 0."""
    if denominator == 0:
        return default
    return numerator / denominator


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a float as a percentage string, e.g. 0.75 → '75.0%'."""
    return f"{value * 100:.{decimals}f}%"


def truncate_text(text: str, max_chars: int = 200, suffix: str = "…") -> str:
    """Truncate *text* to at most *max_chars* characters."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def build_lookup(items: list[Any], key_attr: str) -> dict[str, Any]:
    """Build a dict keyed by *key_attr* from a list of objects/dicts."""
    lookup: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict):
            k = item.get(key_attr)
        else:
            k = getattr(item, key_attr, None)
        if k is not None:
            lookup[str(k)] = item
    return lookup
