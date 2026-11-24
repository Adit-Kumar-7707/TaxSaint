"""
csv_importer.py - TaxSaint Deliverable 2: CSV/Excel transaction import.

Reads a file of income, expense or bank transaction records, checks every row,
and sends the valid rows to the FastAPI backend (never straight to the
database). excel_importer.py reuses everything here except the file reading.

Pipeline:
    read -> clean -> detect type -> check columns -> check rows
         -> split valid/invalid -> convert to API format
         -> (optional) skip existing -> send to FastAPI -> summary

Used in two ways:
    1. Command line:   python -m data_input.importers.csv_importer FILE --user-id 1
    2. Web upload:     process_file_stream() is called by POST /api/financial/upload
"""

import argparse
import io
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

API_URL_ENV = "TAXSAINT_API_BASE_URL"
DEFAULT_API_URL = "http://localhost:8000"
TIMEOUT_SECONDS = 10

# Everything that differs between the three record types. Endpoints and field
# names come from integration/api/routes/financial.py and schemas/requests.py.
RECORD_TYPES = {
    "income": {
        "key_column": "source",                    # column that identifies this type
        "required": ["source", "amount", "date"],
        "optional": ["party_name"],                # backend uses 'source' if missing
        "date_field": "income_date",               # name of the date field in the API
        "endpoint": "/api/financial/income",
        "list_endpoint": "/api/financial/income/{user_id}",
        "match_fields": ["source", "amount", "income_date"],
    },
    "expense": {
        "key_column": "category",
        "required": ["category", "party_name", "amount", "date"],
        "optional": [],
        "date_field": "expense_date",
        "endpoint": "/api/financial/expenses",
        "list_endpoint": "/api/financial/expenses/{user_id}",
        "match_fields": ["category", "party_name", "amount", "expense_date"],
    },
    "bank_transaction": {
        "key_column": "transaction_type",
        "required": ["transaction_type", "amount", "date"],
        "optional": ["party_name"],
        "date_field": "transaction_date",
        "endpoint": "/api/financial/bank-transactions",
        "list_endpoint": None,                     # the API has no list endpoint for these
        "match_fields": None,
    },
}

# Files may call the date column "date" or use the database names.
COLUMN_ALIASES = {"income_date": "date", "expense_date": "date", "transaction_date": "date"}

# Maximum text lengths, from database_manager/schema/data.sql.
MAX_LENGTH = {"source": 50, "category": 50, "party_name": 100}

BANK_DIRECTIONS = ("INCOME", "EXPENSE")
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S")  # last one = Excel dates

# Values of ImportSummary.status
SUCCESS, PARTIAL, FAILED = "success", "partial", "failed"
REJECTED, NO_NEW_RECORDS, DRY_RUN = "rejected", "no_new_records", "dry_run"


class ImporterError(Exception):
    """A problem with the whole file or setup, so the import cannot continue."""


@dataclass
class ValidationError:
    """One problem found in the file. row is the row number (header = row 1)."""
    row: int
    column: str
    message: str


@dataclass
class ImportSummary:
    """What happened during one import (the upload route reads these fields)."""
    file: str
    transaction_type: str = ""
    status: str = FAILED
    dry_run: bool = False
    total_rows: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    duplicate_count: int = 0
    sent_count: int = 0
    errors: list[ValidationError] = field(default_factory=list)
    send_errors: list[str] = field(default_factory=list)
    message: str = ""


# ---------------------------------------------------------------------------
# 1. Reading and cleaning
# ---------------------------------------------------------------------------

def check_file_exists(source) -> None:
    """If source is a path (not an in-memory file), make sure the file exists."""
    if isinstance(source, (str, Path)) and not Path(source).is_file():
        raise ImporterError(f"File not found: {source}")


def read_csv_file(source) -> pd.DataFrame:
    """Read a CSV (a path or an in-memory file) as text, so nothing is guessed."""
    check_file_exists(source)
    try:
        return pd.read_csv(
            source, dtype=str, keep_default_na=False, na_values=[""],
            skip_blank_lines=False,   # keeps row numbers correct
            encoding="utf-8-sig",     # also handles Excel's "CSV UTF-8" files
        )
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        raise ImporterError(f"Could not read the CSV file: {error}") from None


def _clean_cell(value):
    """Strip spaces; empty cells become missing (None / NaN)."""
    if pd.isna(value):
        return None
    return str(value).strip() or None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Tidy headers ("Party Name" -> "party_name"), strip cells, drop empty rows."""
    df = df.copy()
    names = [str(name).strip().lower().replace(" ", "_") for name in df.columns]
    df.columns = [COLUMN_ALIASES.get(name, name) for name in names]
    if df.columns.duplicated().any():
        raise ImporterError("The file has duplicate column names: "
                            + ", ".join(sorted(set(df.columns[df.columns.duplicated()]))))
    df = df.astype(object).apply(lambda column: column.map(_clean_cell))
    return df.dropna(how="all")   # the original row numbers are kept


# ---------------------------------------------------------------------------
# 2. Detecting the record type
# ---------------------------------------------------------------------------

def detect_transaction_type(df: pd.DataFrame) -> str:
    """Return 'income', 'expense' or 'bank_transaction' from the columns present."""
    matches = [name for name, info in RECORD_TYPES.items() if info["key_column"] in df.columns]
    if len(matches) != 1:
        raise ImporterError(
            f"Could not tell the record type from the columns {list(df.columns)}. "
            "Expected exactly one of: source (income), category (expense), "
            "transaction_type (bank_transaction)."
        )
    return matches[0]


# ---------------------------------------------------------------------------
# 3. Column validation
# ---------------------------------------------------------------------------

def validate_columns(df: pd.DataFrame, record_type: str) -> list[str]:
    """Return the required columns that are missing (empty list = all present)."""
    return [column for column in RECORD_TYPES[record_type]["required"] if column not in df.columns]


# ---------------------------------------------------------------------------
# 4. Row validation
# ---------------------------------------------------------------------------

def parse_amount(text: str) -> Decimal:
    """Turn '1,234.50' into Decimal('1234.50'). Raises ValueError if not acceptable."""
    try:
        amount = Decimal(text.replace(",", ""))
    except InvalidOperation:
        raise ValueError("amount is not a number") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be greater than 0")
    if amount >= 10**10:                                  # database column is DECIMAL(12,2)
        raise ValueError("amount is too large")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError("amount has more than 2 decimal places")
    return amount.quantize(Decimal("0.01"))


def parse_date(text: str) -> date:
    """Turn '2026-04-30' or '30/04/2026' into a date. Raises ValueError if not acceptable."""
    for date_format in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, date_format).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError("date must look like 2026-04-30 or 30/04/2026")
    return parsed


def _problem(check, value):
    """Run a parse function; return its error message, or None if the value is fine."""
    try:
        check(value)
    except ValueError as error:
        return str(error)
    return None


def validate_row(row: pd.Series, row_number: int, record_type: str) -> list[ValidationError]:
    """Check one row. Returns its problems (empty list = the row is valid)."""
    info = RECORD_TYPES[record_type]
    errors = []
    for column in info["required"] + info["optional"]:
        value = row.get(column)
        if pd.isna(value):
            if column in info["required"]:
                errors.append(ValidationError(row_number, column, "missing value"))
            continue
        problem = None
        if column == "amount":
            problem = _problem(parse_amount, value)
        elif column == "date":
            problem = _problem(parse_date, value)
        elif column == "transaction_type" and value.upper() not in BANK_DIRECTIONS:
            problem = "must be INCOME or EXPENSE"
        elif column in MAX_LENGTH and len(value) > MAX_LENGTH[column]:
            problem = f"too long (maximum {MAX_LENGTH[column]} characters)"
        if problem:
            errors.append(ValidationError(row_number, column, problem))
    return errors


# ---------------------------------------------------------------------------
# 5. Separating valid and invalid rows
# ---------------------------------------------------------------------------

def split_valid_invalid(df: pd.DataFrame, record_type: str):
    """Return (valid_rows, invalid_rows, errors)."""
    errors = []
    valid_index, invalid_index = [], []
    for index, row in df.iterrows():
        row_errors = validate_row(row, int(index) + 2, record_type)   # +2: header is row 1
        errors.extend(row_errors)
        (invalid_index if row_errors else valid_index).append(index)
    return df.loc[valid_index], df.loc[invalid_index], errors


# ---------------------------------------------------------------------------
# 6. Converting to the API format
# ---------------------------------------------------------------------------

def convert_to_internal_format(valid_df: pd.DataFrame, record_type: str, user_id: int) -> list[dict]:
    """
    Turn valid rows into the JSON the backend expects. Example (income):
    {"user_id": 1, "source": "Salary", "amount": "85000.00", "income_date": "2026-04-30"}
    Amounts are sent as text so no precision is lost.
    """
    info = RECORD_TYPES[record_type]
    records = []
    for _, row in valid_df.iterrows():
        record = {"user_id": user_id}
        for column in info["required"] + info["optional"]:
            value = row.get(column)
            if pd.isna(value):
                continue                      # empty optional column: leave it out
            if column == "amount":
                record["amount"] = str(parse_amount(value))
            elif column == "date":
                record[info["date_field"]] = parse_date(value).isoformat()
            elif column == "transaction_type":
                record[column] = value.upper()
            else:
                record[column] = value
        records.append(record)
    return records


# ---------------------------------------------------------------------------
# 7. Skipping records that already exist (optional)
# ---------------------------------------------------------------------------

def _match_key(record: dict, fields: list[str]) -> tuple:
    """Comparable form of a record ('85000.0' from the database equals '85000.00')."""
    return tuple(
        str(Decimal(str(record[f])).quantize(Decimal("0.01"))) if f == "amount" else str(record.get(f))
        for f in fields
    )


def handle_duplicates(records: list[dict], record_type: str, user_id: int, api_url: str):
    """
    Split records into (new, already_saved) by asking the backend what this user
    already has. Used only when skip_existing is on, for accidental re-uploads.
    By default every record is sent and the fraud engine decides what is suspicious.
    """
    info = RECORD_TYPES[record_type]
    if not records or not info["list_endpoint"]:
        return records, []
    try:
        response = requests.get(api_url + info["list_endpoint"].format(user_id=user_id), timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        existing = response.json()
    except (requests.RequestException, ValueError) as error:
        raise ImporterError(f"Could not check existing records ({error.__class__.__name__}). Is the API running?") from None

    saved = Counter(_match_key(row, info["match_fields"]) for row in existing)
    new, duplicates = [], []
    for record in records:
        key = _match_key(record, info["match_fields"])
        if saved[key] > 0:
            saved[key] -= 1
            duplicates.append(record)
        else:
            new.append(record)
    return new, duplicates


# ---------------------------------------------------------------------------
# 8. Sending to FastAPI
# ---------------------------------------------------------------------------

def _error_detail(response: requests.Response) -> str:
    """The backend's error message (FastAPI puts it under 'detail')."""
    try:
        return str(response.json()["detail"])[:300]
    except (ValueError, KeyError, TypeError):
        return response.text[:300]


def send_to_api(records: list[dict], record_type: str, api_url: str):
    """
    POST the records one at a time. Returns (number_sent, error_messages).
    A record the API rejects is reported and the rest are still sent;
    if the API cannot be reached at all, sending stops.
    """
    url = api_url + RECORD_TYPES[record_type]["endpoint"]
    sent, errors = 0, []
    for record in records:
        try:
            response = requests.post(url, json=record, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as error:
            errors.append(f"Could not reach the API at {url} ({error.__class__.__name__}); stopped.")
            break
        if response.ok:
            sent += 1
        else:
            errors.append(f"{record} -> HTTP {response.status_code}: {_error_detail(response)}")
    return sent, errors


# ---------------------------------------------------------------------------
# 9. Putting it all together
# ---------------------------------------------------------------------------

def process_dataframe(df: pd.DataFrame, file_path, user_id: int, dry_run: bool = False,
                      skip_existing: bool = False, api_base_url: str = None) -> ImportSummary:
    """
    Everything after reading the file; shared by the CSV, Excel and upload paths.
    dry_run        check the file but contact no API and send nothing.
    skip_existing  do not send records the backend already has (income/expense only).
    Row problems are reported in the summary; file problems raise ImporterError.
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ImporterError("user_id must be a positive whole number.")
    api_url = (api_base_url or os.environ.get(API_URL_ENV) or DEFAULT_API_URL).rstrip("/")

    df = clean_dataframe(df)
    if df.empty:
        raise ImporterError("The file has no data rows.")
    record_type = detect_transaction_type(df)
    summary = ImportSummary(str(file_path), record_type, dry_run=dry_run, total_rows=len(df))

    missing = validate_columns(df, record_type)
    if missing:
        summary.errors = [ValidationError(0, column, "required column is missing") for column in missing]
        summary.status = REJECTED
        summary.message = "Missing required column(s): " + ", ".join(missing)
        return summary

    valid_df, invalid_df, summary.errors = split_valid_invalid(df, record_type)
    summary.valid_count, summary.invalid_count = len(valid_df), len(invalid_df)
    records = convert_to_internal_format(valid_df, record_type, user_id)

    if dry_run:
        summary.status = DRY_RUN
        summary.message = f"Dry run: {len(records)} record(s) would be sent, {summary.invalid_count} rejected."
        return summary

    if skip_existing:
        records, duplicates = handle_duplicates(records, record_type, user_id, api_url)
        summary.duplicate_count = len(duplicates)
    if not records:
        summary.status = NO_NEW_RECORDS if summary.valid_count else FAILED
        summary.message = "Nothing new to import." if summary.valid_count else "No valid rows to import."
        return summary

    summary.sent_count, summary.send_errors = send_to_api(records, record_type, api_url)
    summary.message = f"Sent {summary.sent_count} of {len(records)} record(s)."
    if summary.send_errors:
        summary.message += " " + summary.send_errors[0][:200]
    if summary.sent_count == 0:
        summary.status = FAILED
    elif summary.invalid_count or summary.send_errors:
        summary.status = PARTIAL
    else:
        summary.status = SUCCESS
    return summary


def import_csv(file_path, user_id: int, dry_run: bool = False,
               skip_existing: bool = False, api_base_url: str = None) -> ImportSummary:
    """Import one CSV file for the given user."""
    df = read_csv_file(file_path)
    return process_dataframe(df, file_path, user_id, dry_run, skip_existing, api_base_url)


def process_file_stream(file_bytes: bytes, filename: str, user_id: int,
                        api_base_url: str = None) -> ImportSummary:
    """Import a file held in memory. Called by the web upload route (POST /api/financial/upload)."""
    name = filename.lower()
    if name.endswith(".csv"):
        df = read_csv_file(io.BytesIO(file_bytes))
    elif name.endswith((".xlsx", ".xlsm", ".xls")):
        from data_input.importers.excel_importer import read_excel_file
        df = read_excel_file(io.BytesIO(file_bytes))
    elif name.endswith(".pdf"):
        from data_input.importers.pdf_importer import parse_pdf_statement
        df = parse_pdf_statement(file_bytes)
    else:
        raise ImporterError(f"Unsupported file type: {filename}. Use .csv, .xlsx, .xls or .pdf")
    return process_dataframe(df, filename, user_id, api_base_url=api_base_url)


# ---------------------------------------------------------------------------
# Command line (also used by excel_importer.py)
# ---------------------------------------------------------------------------

def make_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", help="path to the file to import")
    parser.add_argument("--user-id", type=int, required=True, help="user the records belong to")
    parser.add_argument("--dry-run", action="store_true", help="check the file only; send nothing")
    parser.add_argument("--skip-existing", action="store_true",
                        help="do not send records the backend already has (accidental re-upload)")
    parser.add_argument("--api-url", help=f"backend URL (default: ${API_URL_ENV} or {DEFAULT_API_URL})")
    return parser


def print_summary(summary: ImportSummary, max_errors: int = 20) -> None:
    print(f"File:        {summary.file}")
    print(f"Record type: {summary.transaction_type}")
    print(f"Status:      {summary.status.upper()}")
    print(f"Rows read:   {summary.total_rows}")
    print(f"Valid:       {summary.valid_count}")
    print(f"Rejected:    {summary.invalid_count}")
    print(f"Skipped:     {summary.duplicate_count}")
    print(f"Sent:        {summary.sent_count}")
    if summary.message:
        print(summary.message)
    for error in summary.errors[:max_errors]:
        where = f"row {error.row}" if error.row else "file"
        print(f"  [{where}] {error.column}: {error.message}")
    if len(summary.errors) > max_errors:
        print(f"  ... and {len(summary.errors) - max_errors} more")
    for message in summary.send_errors[:max_errors]:
        print(f"  [send failed] {message}")


def run_cli(do_import) -> int:
    """Run an import and print the result. Exit code: 0 = clean, 1 = problems, 2 = failed."""
    try:
        summary = do_import()
    except ImporterError as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 2
    print_summary(summary)
    clean = summary.status in (SUCCESS, NO_NEW_RECORDS) or (summary.status == DRY_RUN and not summary.invalid_count)
    return 0 if clean else 1


def main(argv=None) -> int:
    args = make_parser("Import a CSV of income, expense or bank transactions.").parse_args(argv)
    return run_cli(lambda: import_csv(args.file, args.user_id, args.dry_run, args.skip_existing, args.api_url))


if __name__ == "__main__":
    sys.exit(main())
