"""Utility helpers for cleaning Excel data before conversion."""

from __future__ import annotations

import pandas as pd


class DataCleaner:
    """Encapsulates reusable cleaning helpers for the converter."""

    def remove_empty_rows(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Drop rows where every column is empty/NaN."""
        if frame.empty:
            return frame
        return frame.dropna(how='all')

    def strip_text_columns(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Trim whitespace for every textual column in the frame."""
        if frame.empty:
            return frame
        text_cols = frame.select_dtypes(include=['object']).columns
        for column in text_cols:
            frame[column] = frame[column].apply(
                lambda value: value.strip() if isinstance(value, str) else value
            )
        return frame

    def normalize_numeric_strings(self, value):
        """Normalize numeric text so commas are consistent before casting."""
        if isinstance(value, str):
            return value.replace(',', '')
        return value
