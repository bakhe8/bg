import json
import os
import tempfile
import unittest
from typing import Dict

import pandas as pd

from transition.backend.excel_to_json_converter import ExcelToJsonConverter


def create_excel_file(frames: Dict[str, pd.DataFrame]) -> str:
    """Helper to create a temporary Excel file with given sheet frames."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    temp_file.close()
    with pd.ExcelWriter(temp_file.name, engine="openpyxl") as writer:
        for sheet_name, frame in frames.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
    return temp_file.name


class TestExcelToJsonConverter(unittest.TestCase):
    def setUp(self):
        self.converter = ExcelToJsonConverter(clean_data=True)

    def tearDown(self):
        pd.options.mode.chained_assignment = None

    def test_convert_excel_to_json_normalizes_data(self):
        frame = pd.DataFrame(
            {
                "Bank Name": ["Riyad Bank"],
                "Bank Guarantee Number": ["RG12345"],
                "Contract No.": ["PO-7788"],
                "Amount": ["125000"],
                "Validity Date": ["2025/12/31"],
                "Contractor Name": ["شركة ألف"],
                "Attachment Link": ["skip-me"],
            }
        )
        path = create_excel_file({"Sheet1": frame})

        try:
            result = self.converter.convert_excel_to_json(path, sheet_name=0, output_file=None)
            payload = json.loads(result)

            self.assertIn("file_info", payload)
            self.assertEqual(payload["file_info"]["records_count"], 1)
            self.assertIn("Attachment Link", payload["file_info"]["unknown_columns"])

            record = payload["records"][0]
            self.assertEqual(record["bank_name"], "بنك الرياض")
            self.assertEqual(record["guarantee_number"], "RG12345")
            self.assertEqual(record["contract_number"], "PO-7788")
            self.assertEqual(record["company_name"], "شركة ألف")
            self.assertEqual(record["validity_date"], "2025-12-31")
            self.assertEqual(record["amount"], "١٢٥٬٠٠٠٫٠٠")
        finally:
            os.unlink(path)

    def test_missing_required_columns_raises(self):
        frame = pd.DataFrame(
            {
                "Bank Name": ["Riyad Bank"],
                "Contract No.": ["PO-7788"],
                "Amount": ["125000"],
                "Validity Date": ["2025/12/31"],
                "Contractor Name": ["شركة ألف"],
            }
        )
        path = create_excel_file({"Sheet1": frame})

        try:
            with self.assertRaises(ValueError):
                self.converter.convert_excel_to_json(path, sheet_name=0)
        finally:
            os.unlink(path)

    def test_multi_sheet_conversion(self):
        sheet_a = pd.DataFrame(
            {
                "Bank Name": ["SNB"],
                "Bank Guarantee Number": ["SNB-1"],
                "Contract No.": ["PO-1"],
                "Amount": ["1000"],
                "Validity Date": ["2025-01-01"],
                "Contractor Name": ["شركة باء"],
            }
        )
        sheet_b = pd.DataFrame(
            {
                "Bank Name": ["BANQUE SAUDI FRANSI"],
                "Bank Guarantee Number": ["BSF-2"],
                "Contract No.": ["PO-2"],
                "Amount": ["2000"],
                "Validity Date": ["2025-02-01"],
                "Contractor Name": ["شركة جيم"],
            }
        )
        path = create_excel_file({"SheetA": sheet_a, "SheetB": sheet_b})

        try:
            result = self.converter.convert_excel_to_json(path, sheet_name="all")
            payload = json.loads(result)
            self.assertIn("sheets", payload)
            self.assertEqual(len(payload["sheets"]), 2)
            self.assertEqual(payload["sheets"]["SheetA"]["metadata"]["records_count"], 1)
            self.assertEqual(payload["sheets"]["SheetB"]["records"][0]["bank_name"], "البنك السعودي الفرنسي")
        finally:
            os.unlink(path)

    def test_validate_file_checks_extension(self):
        valid_excel = create_excel_file(
            {
                "Sheet1": pd.DataFrame(
                    {
                        "Bank Name": ["Riyad Bank"],
                        "Bank Guarantee Number": ["RG1"],
                        "Contract No.": ["PO-1"],
                        "Amount": ["1000"],
                        "Validity Date": ["2025-12-31"],
                        "Contractor Name": ["شركة"],
                    }
                )
            }
        )
        temp_txt = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        temp_txt.write(b"placeholder")
        temp_txt.close()

        try:
            self.assertTrue(self.converter.validate_file(valid_excel))
            with self.assertRaises(FileNotFoundError):
                self.converter.validate_file("missing.xlsx")
            with self.assertRaises(ValueError):
                self.converter.validate_file(temp_txt.name)
        finally:
            os.unlink(valid_excel)
            os.unlink(temp_txt.name)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
