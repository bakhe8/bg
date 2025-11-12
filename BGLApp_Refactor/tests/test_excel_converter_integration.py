from __future__ import annotations

import json
import os
import tempfile

import pandas as pd
import pytest

from BGLApp_Refactor.core.excel.converter import ExcelConverter


def create_excel_file(frames: dict[str, pd.DataFrame]) -> str:
    """Helper to create a temporary Excel file with given sheet frames."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    temp_file.close()
    with pd.ExcelWriter(temp_file.name, engine="openpyxl") as writer:
        for sheet_name, frame in frames.items():
            frame.to_excel(writer, sheet_name=sheet_name, index=False)
    return temp_file.name


@pytest.fixture()
def converter():
    return ExcelConverter(clean_data=True)


def test_convert_excel_to_json_normalizes_data(converter):
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
        result = converter.convert_to_json(path, sheet=0)
        payload = json.loads(result)

        assert "file_info" in payload
        assert payload["file_info"]["records_count"] == 1
        assert "Attachment Link" in payload["file_info"]["unknown_columns"]

        record = payload["records"][0]
        assert record["guarantee_number"] == "RG12345"
        assert record["contract_number"] == "PO-7788"
        assert record["company_name"] == "شركة ألف"
        assert record["validity_date"] == "2025-12-31"
    finally:
        os.unlink(path)


def test_missing_required_columns_raises(converter):
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
        with pytest.raises(ValueError):
            converter.convert_to_json(path, sheet=0)
    finally:
        os.unlink(path)


def test_multi_sheet_conversion(converter):
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
        result = converter.convert_to_json(path, sheet="all")
        payload = json.loads(result)
        assert "sheets" in payload
        assert len(payload["sheets"]) == 2
    finally:
        os.unlink(path)


def test_validate_file_checks_extension(converter):
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
        assert converter._impl.validate_file(valid_excel)  # type: ignore[attr-defined]
        with pytest.raises(FileNotFoundError):
            converter._impl.validate_file("missing.xlsx")  # type: ignore[attr-defined]
        with pytest.raises(ValueError):
            converter._impl.validate_file(temp_txt.name)  # type: ignore[attr-defined]
    finally:
        os.unlink(valid_excel)
        os.unlink(temp_txt.name)
