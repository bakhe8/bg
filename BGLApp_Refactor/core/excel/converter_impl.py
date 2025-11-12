from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

from BGLApp_Refactor.core.config.paths import LEGACY_PATHS
from .data_pipeline import ColumnMapper, DataCleaner, DataValidator, ExcelPreprocessor, PipelineLogger
from .reference_loader import load_bank_reference, load_column_aliases, load_normalization_rules

DEFAULT_REPORTS_DIR = LEGACY_PATHS.root_dir / "transition" / "backend" / "reports"

# كتم تحذيرات pandas غير الضرورية
warnings.filterwarnings("ignore")


class ExcelToJsonConverter:
    """High-level façade that orchestrates the Excel → JSON pipeline."""

    ARABIC_TO_EN = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789..")

    def __init__(
        self,
        clean_data: bool = True,
        optimize_memory: bool = True,
        log_path: str | Path | None = None,
    ) -> None:
        self.supported_formats = [".xlsx", ".xls"]
        self.clean_data = clean_data
        self.optimize_memory = optimize_memory

        self.normalization_rules = load_normalization_rules()
        self.column_aliases = load_column_aliases()
        self.bank_reference = load_bank_reference()
        self.bank_lookup = self._build_bank_lookup(self.bank_reference)
        self.required_columns = self.normalization_rules.get(
            "required_fields",
            list(self.column_aliases.keys()),
        )

        log_file = Path(log_path) if log_path else DEFAULT_REPORTS_DIR / "pipeline.log"
        self.preprocessor = self._build_preprocessor(log_file)

        self.check_dependencies()

    def _build_preprocessor(self, log_file: Path) -> ExcelPreprocessor:
        column_mapper = ColumnMapper(self.column_aliases, required_fields=self.required_columns)
        cleaner = DataCleaner(self.normalization_rules)
        validator = DataValidator()
        logger = PipelineLogger(log_file)
        return ExcelPreprocessor(
            column_mapper=column_mapper,
            cleaner=cleaner,
            validator=validator,
            bank_lookup=self.bank_lookup,
            normalization_rules=self.normalization_rules,
            logger=logger,
            clean_enabled=self.clean_data,
        )

    def _build_bank_lookup(self, entries: List[Dict[str, Any]]) -> Dict[str, str]:
        lookup: Dict[str, str] = {}
        for entry in entries:
            arabic = entry.get("arabic", "").strip()
            aliases = entry.get("aliases", [])
            if not arabic:
                continue
            lookup[self._normalize_label(arabic)] = arabic
            for alias in aliases:
                lookup[self._normalize_label(alias)] = arabic
        return lookup

    def _normalize_label(self, value: str) -> str:
        return " ".join(str(value).strip().lower().split())

    def check_dependencies(self) -> None:
        """التحقق من وجود المكتبات المطلوبة."""
        try:
            import pandas  # pylint:disable=unused-import
            import openpyxl  # pylint:disable=unused-import
        except ImportError as exc:  # pragma: no cover - defensive branch
            print("❌ المكتبات المطلوبة غير مثبتة!")
            print("📦 قم بتثبيتها باستخدام:")
            print("   pip install pandas openpyxl")
            raise

    def validate_file(self, file_path: str) -> bool:
        """تأكد من أن الملف موجود وذو صيغة مدعومة."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"الملف '{file_path}' غير موجود")

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"الصيغة '{file_ext}' غير مدعومة. الصيغ المدعومة: {self.supported_formats}")

        return True

    def read_excel_optimized(self, file_path: str, sheet_name: str | int | None = 0):
        """قراءة ملف Excel مع خيارات تحكم بالذاكرة."""
        read_options: Dict[str, Any] = {
            "sheet_name": sheet_name,
            "keep_default_na": False,
            "na_values": ["", " ", "NULL", "null"],
        }

        if self.optimize_memory:
            read_options.update({"dtype": object, "usecols": None})

        if sheet_name == "all":
            read_options["sheet_name"] = None

        try:
            return pd.read_excel(file_path, **read_options)
        except Exception as exc:  # pragma: no cover - detailed message handled upstream
            raise Exception(f"خطأ في قراءة الملف: {exc}") from exc

    def convert_excel_to_json(self, excel_file: str, sheet_name: str | int = 0, output_file: str | None = None) -> str:
        """الدالة الرئيسية للتحويل مع استخدام خط الأنابيب الجديد."""
        self.validate_file(excel_file)
        data = self.read_excel_optimized(excel_file, sheet_name)

        if isinstance(data, dict):
            result = self._process_multiple_sheets(data, excel_file, output_file)
        else:
            result = self._process_single_sheet(data, excel_file, sheet_name, output_file)

        del data
        return result

    def _process_single_sheet(
        self,
        frame: pd.DataFrame,
        excel_file: str,
        sheet_name: str | int,
        output_file: str | None,
    ) -> str:
        metadata = self._base_metadata(excel_file, sheet_name)
        processed = self.preprocessor.process(frame, metadata)

        payload = {
            "file_info": self._collect_file_info(metadata, processed, sheet_name),
            "columns": list(processed.columns),
            "data_types": self._describe_columns(processed),
            "records": self._frame_to_records(processed),
        }
        return self.save_output(payload, output_file)

    def _process_multiple_sheets(
        self,
        sheets: Dict[str, pd.DataFrame],
        excel_file: str,
        output_file: str | None,
    ) -> str:
        processed_sheets: Dict[str, Dict[str, Any]] = {}
        aggregated_unknown: Dict[str, List[str]] = {}

        for sheet_name, frame in sheets.items():
            metadata = self._base_metadata(excel_file, sheet_name)
            processed = self.preprocessor.process(frame, metadata)
            processed_sheets[sheet_name] = {
                "metadata": self._collect_sheet_metadata(metadata, processed),
                "data_types": self._describe_columns(processed),
                "records": self._frame_to_records(processed),
            }
            aggregated_unknown[sheet_name] = metadata.get("unknown_columns", [])

        file_info = {
            "file_name": os.path.basename(excel_file),
            "conversion_date": self._now_iso(),
            "total_sheets": len(processed_sheets),
            "cleaning_applied": self.clean_data,
            "unknown_columns": aggregated_unknown,
        }

        payload = {
            "file_info": file_info,
            "sheets": processed_sheets,
        }
        return self.save_output(payload, output_file)

    def _collect_file_info(self, metadata: Dict[str, Any], frame: pd.DataFrame, sheet_name: str | int) -> Dict[str, Any]:
        return {
            "file_name": metadata["file_name"],
            "sheet_name": sheet_name,
            "conversion_date": self._now_iso(),
            "records_count": metadata.get("rows_after", len(frame)),
            "columns_count": len(frame.columns),
            "cleaning_applied": self.clean_data,
            "unknown_columns": metadata.get("unknown_columns", []),
        }

    def _collect_sheet_metadata(self, metadata: Dict[str, Any], frame: pd.DataFrame) -> Dict[str, Any]:
        return {
            "records_count": metadata.get("rows_after", len(frame)),
            "columns_count": len(frame.columns),
            "cleaning_applied": self.clean_data,
            "unknown_columns": metadata.get("unknown_columns", []),
        }

    def _base_metadata(self, excel_file: str, sheet_name: str | int) -> Dict[str, Any]:
        return {
            "file_name": os.path.basename(excel_file),
            "sheet_name": str(sheet_name),
            "timestamp": self._now_iso(),
        }

    def _describe_columns(self, frame: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        types: Dict[str, Dict[str, Any]] = {}
        for column in frame.columns:
            series = frame[column]
            sample = self._sample_value(series)
            types[column] = {
                "type": self._infer_type(series),
                "sample": sample,
                "distinct_count": int(series.nunique(dropna=True)),
            }
        return types

    def _sample_value(self, series: pd.Series) -> Any:
        for value in series:
            if value is not None and str(value).strip():
                return value
        return ""

    def _infer_type(self, series: pd.Series) -> str:
        non_empty = [value for value in series.dropna() if str(value).strip()]
        if not non_empty:
            return "empty"
        if self._looks_like_date(non_empty):
            return "date_like"
        if self._looks_like_numeric(non_empty):
            return "numeric_string"
        return "text"

    def _looks_like_date(self, values: Iterable[Any]) -> bool:
        try:
            parsed = pd.to_datetime(pd.Series(values), errors="coerce")
            if parsed.empty:
                return False
            ratio = parsed.notna().sum() / len(parsed)
            return ratio >= 0.8
        except Exception:
            return False

    def _looks_like_numeric(self, values: Iterable[Any]) -> bool:
        success = 0
        total = 0
        for value in values:
            total += 1
            text = self._to_english_digits(str(value))
            text = text.replace(",", "").replace(" ", "").replace("SAR", "").replace("ريال", "")
            text = text.replace("٫", ".").replace("٬", "")
            if self._is_float(text):
                success += 1
        if total == 0:
            return False
        return (success / total) >= 0.8

    def _to_english_digits(self, value: str) -> str:
        return value.translate(self.ARABIC_TO_EN)

    @staticmethod
    def _is_float(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _frame_to_records(self, frame: pd.DataFrame) -> List[Dict[str, Any]]:
        sanitized = frame.copy()
        sanitized = sanitized.where(~sanitized.isna(), None)
        return sanitized.to_dict(orient="records")

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def save_output(self, result_data: Dict[str, Any], output_file: str | None) -> str:
        json_output = json.dumps(result_data, ensure_ascii=False, indent=2, default=str)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_output, encoding="utf-8")
            print(f"💾 تم حفظ النتائج في: {output_path}")

        return json_output

    def get_sheet_names(self, excel_file: str) -> List[str]:
        """إرجاع أسماء الأوراق لمساعدة الواجهة التفاعلية."""
        self.validate_file(excel_file)
        try:
            workbook = pd.ExcelFile(excel_file)
            return workbook.sheet_names
        except Exception:
            return []


def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="برنامج تحويل Excel إلى JSON بخوارزمية التنظيف الذكي",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  %(prog)s data.xlsx                    # تحويل الورقة الأولى
  %(prog)s data.xlsx --sheet all        # تحويل جميع الأوراق
  %(prog)s data.xlsx --no-clean         # بدون تنظيف البيانات
  %(prog)s data.xlsx -o output.json     # تحديد ملف الإخراج
        """,
    )

    parser.add_argument("file", help="مسار ملف Excel المدخل")
    parser.add_argument("--sheet", default=0, help='اسم الورقة أو "all" لجميع الأوراق (افتراضي: الأولى)')
    parser.add_argument("-o", "--output", help="ملف JSON الإخراج (اختياري)")
    parser.add_argument("--no-clean", action="store_true", help="تعطيل تنظيف البيانات")
    parser.add_argument("--no-optimize", action="store_true", help="تعطيل تحسين الذاكرة")
    return parser


def main() -> None:
    """تشغيل المحول من سطر الأوامر."""
    parser = setup_argparse()
    if len(sys.argv) <= 1:
        print("🔄 برنامج تحويل Excel إلى JSON")
        print("=" * 50)
        return

    args = parser.parse_args()
    converter = ExcelToJsonConverter(clean_data=not args.no_clean, optimize_memory=not args.no_optimize)

    try:
        result = converter.convert_excel_to_json(args.file, args.sheet, args.output)
        data = json.loads(result)
        if "sheets" in data:
            total_records = sum(sheet["metadata"]["records_count"] for sheet in data["sheets"].values())
            print(f"✅ تم التحويل بنجاح: {len(data['sheets'])} أوراق، {total_records} سجل")
        else:
            print(f"✅ تم التحويل بنجاح: {data['file_info']['records_count']} سجل")
    except Exception as exc:  # pragma: no cover - CLI convenience
        print(f"❌ {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
