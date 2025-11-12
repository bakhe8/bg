"""
Compatibility shim for legacy ExcelToJsonConverter tests.

It copies the public API of the legacy implementation while making
small behaviour tweaks that the historic unit tests expect (مثل
إرجاع نوع ``mixed`` للأعمدة المختلطة والتحقق من الامتداد قبل
وجود الملف). هذا يحافظ على الملف الأصلي دون تعديل.
"""

from __future__ import annotations

import math
import os

from legacy.exceltojson.excel_to_json_converter import ExcelToJsonConverter as _LegacyExcelToJsonConverter


class ExcelToJsonConverter(_LegacyExcelToJsonConverter):
    """Wrapper around the legacy converter with test-friendly semantics."""

    SUCCESS_MESSAGE = "تم التحويل بنجاح"

    def convert_excel_to_json(self, excel_file, sheet_name=0, output_file=None):  # type: ignore[override]
        result = super().convert_excel_to_json(excel_file, sheet_name, output_file)
        return result, self.SUCCESS_MESSAGE

    def validate_file(self, file_path: str) -> bool:  # type: ignore[override]
        extension = os.path.splitext(file_path)[1].lower()
        if extension and extension not in self.supported_formats:
            raise ValueError(f"الصيغة '{extension}' غير مدعومة. الصيغ المدعومة: {self.supported_formats}")
        return super().validate_file(file_path)

    def analyze_column(self, series, sample_data):  # type: ignore[override]
        analysis = super().analyze_column(series, sample_data)
        if analysis.get("mixed_types"):
            analysis["type"] = "mixed"
        return analysis

    def detect_data_types_improved(self, df):  # type: ignore[override]
        results = super().detect_data_types_improved(df)
        for info in results.values():  # type: ignore[assignment]
            if isinstance(info, dict) and info.get("mixed_types"):
                info["type"] = "mixed"
        return results

    def save_output(self, result_data, output_file=None):  # type: ignore[override]
        sanitized = self._sanitize_for_json(result_data)
        return super().save_output(sanitized, output_file)

    def _sanitize_for_json(self, value):
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return ""
            return value
        if isinstance(value, dict):
            return {k: self._sanitize_for_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._sanitize_for_json(item) for item in value]
        return value


__all__ = ["ExcelToJsonConverter"]
