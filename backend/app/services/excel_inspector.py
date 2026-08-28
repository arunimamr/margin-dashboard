from pathlib import Path
from typing import Any

import pandas as pd


def inspect_excel(path: str | Path, rows: int = 5) -> dict[str, Any]:
    workbook = pd.ExcelFile(path)
    sheets: list[dict[str, Any]] = []
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet_name)
        sheets.append(
            {
                "name": sheet_name,
                "columns": [str(column) for column in frame.columns],
                "row_count": len(frame),
                "sample_rows": frame.head(rows).where(frame.notna(), None).to_dict(orient="records"),
                "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
            }
        )
    return {"path": str(path), "sheets": sheets}


def inspect_workbook(path: str | Path, rows: int = 5) -> dict[str, Any]:
    return inspect_excel(path, rows=rows)