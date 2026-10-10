"""
excel_importer.py

TaxSaint - Deliverable 2: CSV/Excel Transaction Import
Excel importer for income, expense, and bank transaction records.

Only the READING step is Excel-specific. Everything after that (cleaning, type
detection, validation, conversion, duplicates, API sending) is shared and lives
in csv_importer.py, so it is imported from there.

Pipeline:
    Excel -> read -> [shared pipeline: csv_importer.process_dataframe]

Responsibility boundary:
    - DATA IMPORT only. No tax calculation, fraud detection, or dashboard logic.
    - No direct Supabase access. Records go through FastAPI.

Usage (from the project root):
    python -m data_input.importers.excel_importer transactions.xlsx --user-id 1
    python -m data_input.importers.excel_importer transactions.xlsx --user-id 1 --sheet Expenses
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

import pandas as pd

try:  # normal case: imported as part of the project package
    from data_input.importers.csv_importer import (
        ImporterError,
        ImportSummary,
        add_common_arguments,
        exit_code_for,
        options_from_args,
        print_summary,
        process_dataframe,
    )
except ModuleNotFoundError:  # run directly as a script from the importers folder
    from csv_importer import (  # type: ignore[no-redef]
        ImporterError,
        ImportSummary,
        add_common_arguments,
        exit_code_for,
        options_from_args,
        print_summary,
        process_dataframe,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS: tuple[str, ...] = (".xlsx", ".xlsm", ".xls")


# ---------------------------------------------------------------------------
# 1. Reading (Excel-specific)
# ---------------------------------------------------------------------------

def _check_excel_path(file_path: str | Path) -> Path:
    path = Path(file_path)
    if not path.is_file():
        raise ImporterError(f"File not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ImporterError(
            f"Unsupported file type '{path.suffix}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return path


def list_sheets(file_path: str | Path) -> list[str]:
    """Return the sheet names in an Excel workbook."""
    path = _check_excel_path(file_path)
    try:
        with pd.ExcelFile(path) as workbook:
            return [str(name) for name in workbook.sheet_names]
    except Exception as exc:  # corrupted / password-protected / missing engine
        raise ImporterError(f"Could not open {path.name}: {exc}") from None


def read_excel_file(
    file_path: str | Path,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """
    Read one sheet of an Excel file into a DataFrame of strings.

    The first row of the sheet must be the header. Everything is read as text
    (no type guessing) so validation sees what the cell shows; date cells
    arrive as "YYYY-MM-DD HH:MM:SS", which the shared date parser accepts.

    Raises ImporterError if the file/sheet is missing, unreadable, or empty.
    """
    path = _check_excel_path(file_path)
    try:
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            dtype=str,
            keep_default_na=False,
            na_values=[""],
        )
    except ValueError as exc:  # unknown sheet name / index
        raise ImporterError(f"Could not read sheet {sheet_name!r} of {path.name}: {exc}") from None
    except ImportError as exc:  # openpyxl / xlrd not installed
        raise ImporterError(f"Missing Excel support library: {exc}. Run: pip install -r requirements.txt") from None
    except Exception as exc:  # corrupted file, password protected, ...
        raise ImporterError(f"Could not read {path.name}: {exc}") from None

    if df.empty:
        raise ImporterError(f"Sheet {sheet_name!r} of {path.name} has no data rows.")
    return df


# ---------------------------------------------------------------------------
# 2. Orchestration
# ---------------------------------------------------------------------------

def import_excel(
    file_path: str | Path,
    user_id: int,
    sheet_name: str | int = 0,
    **options: Any,
) -> ImportSummary:
    """
    Run the full import workflow for one Excel sheet.

    options are passed to csv_importer.process_dataframe() (forced_type,
    dry_run, strict, check_duplicates, api_base_url, ledger_path, rejected_out).
    Raises ImporterError for file-level problems.
    """
    df = read_excel_file(file_path, sheet_name)
    return process_dataframe(df, file_path, user_id, **options)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """Command-line entry point for Excel files. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        description="Import an Excel sheet of income, expense or bank transactions into TaxSaint."
    )
    parser.add_argument("file", help="path to the .xlsx / .xls file")
    parser.add_argument("--sheet", default="0",
                        help="sheet name or 0-based index (default: first sheet)")
    parser.add_argument("--list-sheets", action="store_true",
                        help="print the sheet names and exit")
    add_common_arguments(parser)
    args = parser.parse_args(argv)
    if args.user_id is None and not args.list_sheets:
        parser.error("--user-id is required")

    sheet: str | int = int(args.sheet) if args.sheet.isdigit() else args.sheet
    try:
        if args.list_sheets:
            for name in list_sheets(args.file):
                print(name)
            return 0
        summary = import_excel(args.file, args.user_id, sheet, **options_from_args(args))
    except ImporterError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 2
    print_summary(summary)
    return exit_code_for(summary)


if __name__ == "__main__":
    sys.exit(main())
