from __future__ import annotations

import json
from unittest import mock

import pytest

from BGLApp_Refactor.core.excel.converter import ExcelConverter


def test_convert_to_json_delegates_to_legacy(monkeypatch):
    legacy_mock = mock.Mock()
    factory = mock.Mock(return_value=legacy_mock)
    monkeypatch.setattr(
        "BGLApp_Refactor.core.excel.converter.PipelineConverter",
        factory,
    )

    converter = ExcelConverter(example="flag")
    converter.convert_to_json("sample.xlsx", sheet="all", output_file="out.json")

    factory.assert_called_once_with(example="flag")
    legacy_mock.convert_excel_to_json.assert_called_once_with(
        "sample.xlsx",
        sheet_name="all",
        output_file="out.json",
    )


def test_convert_to_dict_parses_json(monkeypatch):
    converter = ExcelConverter.__new__(ExcelConverter)
    converter._impl = mock.Mock()  # type: ignore[attr-defined]
    monkeypatch.setattr(
        converter,
        "convert_to_json",
        mock.Mock(return_value=json.dumps({"rows": 2})),
    )

    payload = converter.convert_to_dict("sample.xlsx")

    assert payload == {"rows": 2}
    converter.convert_to_json.assert_called_once()


@pytest.mark.parametrize(
    "provided,expected",
    [
        (("xls", "xlsx", "xlsm"), ("xls", "xlsx", "xlsm")),
        (None, (".xls", ".xlsx")),
    ],
)
def test_supported_extensions_has_reasonable_defaults(provided, expected, monkeypatch):
    converter = ExcelConverter.__new__(ExcelConverter)
    converter._impl = mock.Mock(  # type: ignore[attr-defined]
        supported_formats=provided
    )

    assert tuple(converter.supported_extensions()) == expected
