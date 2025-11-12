"""
Excel conversion façade for the refactor workspace.

The converter now lives fully inside the refactor tree while keeping the
same public API the legacy stack expects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from .converter_impl import ExcelToJsonConverter as PipelineConverter


class ExcelConverter:
    """
    Thin wrapper that keeps behaviour identical while giving us a modern API.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._impl = PipelineConverter(**kwargs)

    def convert_to_json(
        self,
        file_path: str | Path,
        sheet: str | int = 0,
        *,
        output_file: str | Path | None = None,
    ) -> str:
        return self._impl.convert_excel_to_json(
            str(file_path),
            sheet_name=sheet,
            output_file=str(output_file) if output_file else None,
        )

    def convert_to_dict(self, file_path: str | Path, sheet: str | int = 0) -> Dict[str, Any]:
        return json.loads(self.convert_to_json(file_path, sheet))

    def supported_extensions(self) -> Iterable[str]:
        formats = getattr(self._impl, "supported_formats", None)
        if not formats:
            return (".xls", ".xlsx")
        return tuple(formats)


__all__ = ["ExcelConverter"]
