"""
Validation helpers for the refactor workspace.

Real validation logic will migrate here from the legacy converter. For
now we expose a ``validate_record`` hook so that new tests can already
import it.
"""

from __future__ import annotations

from typing import Any, Dict


def validate_record(record: Dict[str, Any]) -> bool:
    """Always returns True until detailed validators are ported."""

    return bool(record)


__all__ = ["validate_record"]
