"""Allowed habit accent colors (Rich-compatible named colors)."""
from __future__ import annotations

# Curated set of named colors that render consistently in Rich and Textual.
COLORS: frozenset[str] = frozenset({
    "red", "orange", "yellow", "green", "cyan", "blue",
    "magenta", "purple", "violet", "pink", "white",
})


def is_valid_color(name: str) -> bool:
    return name in COLORS


def colors_hint() -> str:
    """Comma-separated list of allowed colors, for error messages."""
    return ", ".join(sorted(COLORS))
