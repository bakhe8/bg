"""Validation helpers used by the ExcelToJsonConverter."""

from __future__ import annotations

from typing import Iterable


class DataValidator:
    """Lightweight validation for spreadsheet content."""

    def ensure_required_columns(self, columns: Iterable[str], required: Iterable[str]) -> None:
        missing = [col for col in required if col not in columns]
        if missing:
            raise ValueError(f"الأعمدة الإلزامية مفقودة: {', '.join(missing)}")

    def coerce_none(self, value):
        """Convert pandas NaN/None-like values to literal None."""
        try:
            import pandas as pd  # محليًا لتفادي الاعتماد في وقت التحميل
            if pd.isna(value):
                return None
        except Exception:  # pragma: no cover - fallback when pandas غير متاح هنا
            pass
        return value
