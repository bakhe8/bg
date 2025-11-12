from __future__ import annotations

from pathlib import Path
from transition.backend import ExcelToJsonConverter


class ApiGateway:
    """Entry point that will be consumed by the production API layer."""

    def __init__(self, archive_dir: Path):
        self.archive_dir = archive_dir
        self.converter = ExcelToJsonConverter()

    def convert_excel(self, file_path: str, sheet: str | int = 0) -> str:
        return self.converter.convert_excel_to_json(file_path, sheet_name=sheet, output_file=None)
