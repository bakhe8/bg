from __future__ import annotations

from typing import Iterable

import pandas as pd


class DataValidator:
    """Validation helpers to ensure cleaned frames satisfy the business rules."""

    def ensure_required_columns(self, columns: Iterable[str], required: Iterable[str]) -> None:
        missing = [col for col in required if col not in columns]
        if missing:
            raise ValueError(f"الأعمدة الإلزامية مفقودة: {', '.join(missing)}")

    def validate_required_fields(self, frame: pd.DataFrame) -> None:
        if frame.isnull().any().any():
            null_columns = frame.columns[frame.isnull().any()].tolist()
            raise ValueError(f"بعض الحقول تحتوي على قيم فارغة: {', '.join(null_columns)}")

    def validate_amounts(self, frame: pd.DataFrame) -> None:
        if "amount" not in frame.columns:
            return
        for value in frame["amount"]:
            if not value:
                raise ValueError("قيمة مبلغ مفقودة")

    def validate_dates(self, frame: pd.DataFrame) -> None:
        if "validity_date" not in frame.columns:
            return
        if frame["validity_date"].isna().any():
            raise ValueError("بعض تواريخ الانتهاء غير صالحة")
