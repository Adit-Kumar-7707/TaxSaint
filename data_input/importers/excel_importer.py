"""
excel_importer.py - TaxSaint Deliverable 2: CSV/Excel transaction import.

The same as csv_importer.py, except for how the file is read. Cleaning,
validation, sending and the summary are all reused from csv_importer.py.

Run from the project root:
    python -m data_input.importers.excel_importer transactions.xlsx --user-id 1 --sheet Expenses
"""

import sys

import pandas as pd

from data_input.importers.csv_importer import (
    ImporterError,
    ImportSummary,
    check_file_exists,
    make_parser,
    process_dataframe,
    run_cli,
)


def read_excel_file(source, sheet_name=0) -> pd.DataFrame:
    """
    Read one sheet of an Excel file (a path or an in-memory file) as text.
    The first row must be the header. Date cells arrive as '2026-04-30 00:00:00'.
    """
    check_file_exists(source)
    try:
        return pd.read_excel(source, sheet_name=sheet_name, dtype=str,
                             keep_default_na=False, na_values=[""])
    except Exception as error:   # wrong sheet name, corrupted file, not an Excel file...
        raise ImporterError(f"Could not read the Excel file: {error}") from None


def import_excel(file_path, user_id: int, sheet_name=0, dry_run: bool = False,
                 skip_existing: bool = False, api_base_url: str = None) -> ImportSummary:
    """Import one sheet of an Excel file for the given user."""
    df = read_excel_file(file_path, sheet_name)
    return process_dataframe(df, file_path, user_id, dry_run, skip_existing, api_base_url)


def main(argv=None) -> int:
    parser = make_parser("Import an Excel sheet of income, expense or bank transactions.")
    parser.add_argument("--sheet", default="0", help="sheet name or number (default: the first sheet)")
    args = parser.parse_args(argv)
    sheet = int(args.sheet) if args.sheet.isdigit() else args.sheet
    return run_cli(lambda: import_excel(args.file, args.user_id, sheet, args.dry_run,
                                        args.skip_existing, args.api_url))


if __name__ == "__main__":
    sys.exit(main())
