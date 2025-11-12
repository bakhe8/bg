from __future__ import annotations

from typing import Dict, List

import pandas as pd

from .column_mapper import ColumnMapper
from .data_cleaner import DataCleaner
from .pipeline_logger import PipelineLogger
from .validator import DataValidator


class ExcelPreprocessor:
    """Coordinate column mapping, cleaning, normalization, validation and logging."""

    def __init__(
        self,
        column_mapper: ColumnMapper,
        cleaner: DataCleaner,
        validator: DataValidator,
        bank_lookup: Dict[str, str],
        normalization_rules: Dict[str, List[str]],
        logger: PipelineLogger,
        clean_enabled: bool = True,
    ) -> None:
        self.column_mapper = column_mapper
        self.cleaner = cleaner
        self.validator = validator
        self.bank_lookup = bank_lookup
        self.normalization_rules = normalization_rules
        self.required_fields = normalization_rules.get("required_fields", column_mapper.required_fields)
        self.clean_enabled = clean_enabled
        self.logger = logger

    def process(self, frame: pd.DataFrame, metadata: Dict[str, str]) -> pd.DataFrame:
        rename_map, unknown = self.column_mapper.map_columns(frame.columns)
        metadata["unknown_columns"] = unknown
        df = frame.rename(columns=rename_map)
        self.validator.ensure_required_columns(df.columns, self.required_fields)
        df = df[self.required_fields].copy()

        metadata.setdefault("rows_before", len(df))
        metadata.setdefault("columns_before", len(df.columns))

        if self.clean_enabled:
            df = self.cleaner.remove_empty_rows(df)
            df = self.cleaner.strip_text_columns(df)
            df = self.cleaner.apply_rules(df)

        df["bank_name"] = df["bank_name"].apply(self._normalize_bank)
        df = self._replace_empty_with_na(df)

        self.validator.validate_required_fields(df)
        self.validator.validate_dates(df)
        self.validator.validate_amounts(df)

        metadata["rows_after"] = len(df)
        metadata["columns_after"] = len(df.columns)
        self.logger.log("success", metadata)
        return df

    def _normalize_bank(self, value: str) -> str:
        if not value:
            return value
        key = " ".join(str(value).strip().lower().split())
        return self.bank_lookup.get(key, str(value).strip())

    def _replace_empty_with_na(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        for column in result.columns:
            result[column] = result[column].apply(self._empty_to_na)
        return result

    @staticmethod
    def _empty_to_na(value):
        if value is None:
            return pd.NA
        if isinstance(value, str) and not value.strip():
            return pd.NA
        return value
