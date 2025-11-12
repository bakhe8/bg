from __future__ import annotations

import pandas as pd


class DataCleaner:
    """Utility methods to normalize DataFrame values according to rules."""

    ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    ENGLISH_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

    def __init__(self, normalization_rules: dict | None = None) -> None:
        self.rules = normalization_rules or {}

    def remove_empty_rows(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        return frame.dropna(how="all")

    def strip_text_columns(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        result = frame.copy()
        text_cols = result.select_dtypes(include=["object"]).columns
        for col in text_cols:
            result[col] = result[col].apply(lambda value: value.strip() if isinstance(value, str) else value)
        return result

    def apply_rules(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Apply normalization rules (text, numeric, date) to a frame."""
        result = frame.copy()
        for column in self.rules.get("text_fields", []):
            if column in result.columns:
                result[column] = result[column].apply(self._normalize_text)

        for column in self.rules.get("numeric_fields", []):
            if column in result.columns:
                result[column] = result[column].apply(self._format_currency)

        for column in self.rules.get("date_fields", []):
            if column in result.columns:
                result[column] = self._format_date_column(result[column])

        return result

    def _format_date_column(self, series: pd.Series) -> pd.Series:
        parsed = pd.to_datetime(series, errors="coerce")
        return parsed.dt.strftime("%Y-%m-%d")

    def _normalize_text(self, value):
        if value is None:
            return ""
        return str(value).strip()

    def _format_currency(self, value):
        if value is None or value == "":
            return ""
        text = str(value).strip()
        text = (
            text.replace(",", "")
            .replace("٬", "")
            .replace("SAR", "")
            .replace("ريال", "")
            .replace("٫", ".")
            .strip()
        )
        text = text.translate(self.ENGLISH_DIGITS)
        try:
            numeric = float(text)
        except ValueError as exc:
            raise ValueError(f"قيمة مبلغ غير صالحة: {value}") from exc
        english = f"{numeric:,.2f}"
        arabic = english.replace(",", "٬").replace(".", "٫").translate(self.ARABIC_DIGITS)
        return arabic
