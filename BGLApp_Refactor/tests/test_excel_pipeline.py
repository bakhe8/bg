from __future__ import annotations

import pandas as pd

from BGLApp_Refactor.core.excel.data_pipeline import ColumnMapper, DataCleaner


def test_column_mapper_handles_exact_and_unknown():
    mapper = ColumnMapper({"bank_name": ["bank name"]})
    rename, unknown = mapper.map_columns(["Bank Name", "Mystery"])
    assert rename["Bank Name"] == "bank_name"
    assert unknown == ["Mystery"]


def test_data_cleaner_formats_currency():
    cleaner = DataCleaner({"numeric_fields": ["amount"]})
    frame = pd.DataFrame({"amount": ["1,200.50", " ٢٥٠٫٧٥ "]})
    result = cleaner.apply_rules(frame)
    assert result.loc[0, "amount"].startswith("١٬")
    assert "٢٥٠" in result.loc[1, "amount"]
