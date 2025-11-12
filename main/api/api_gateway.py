from __future__ import annotations

from pathlib import Path

from BGLApp_Refactor.core.excel.converter import ExcelConverter

class ApiGateway:
    """Entry point that will be consumed by the production API layer."""

    def __init__(self, archive_dir: Path):
        self.archive_dir = archive_dir
        self.converter = ExcelConverter()

    def convert_excel(self, file_path: str, sheet: str | int = 0) -> str:
        return self.converter.convert_to_json(file_path, sheet)
