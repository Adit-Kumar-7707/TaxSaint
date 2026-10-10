"""
csv_importer.py

TaxSaint - Deliverable 2: CSV/Excel Transaction Import
CSV importer for income, expense, and bank transaction records.

This module also holds the SHARED import pipeline (type detection, validation,
conversion, duplicate handling, API sending). excel_importer.py reuses these
functions so the logic exists in exactly one place.

Pipeline:
    CSV -> read -> clean -> detect type -> validate columns -> validate rows
        -> separate valid/invalid -> convert to internal format
        -> duplicate check -> send to FastAPI -> import summary

Responsibility boundary:
    - This module handles DATA IMPORT only.
    - It does NOT calculate tax, detect fraud, or touch the dashboard.
    - It does NOT connect to Supabase. Valid records go through FastAPI.

Alignment with the rest of TaxSaint:
    - Column names / lengths follow database_manager/schema/data.sql.
    - Endpoints and payload field names follow frontend/src/services/api.js
      and the frontend forms (the only existing API client). The whole
      mapping lives in API_ENDPOINTS / API_FIELD_MAP below, so changing it
      when the backend schema is finalized is a one-place edit.

Usage (from the project root):
    python -m data_input.importers.csv_importer income.csv --user-id 1
    python -m data_input.importers.csv_importer income.csv --user-id 1 --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TransactionType(str, Enum):
    """Kinds of records the importer supports."""
    INCOME = "income"
    EXPENSE = "expense"
    BANK_TRANSACTION = "bank_transaction"


class ImporterError(Exception):
    """A file-level problem that stops the import (unreadable file, unknown type...)."""


# Required input columns per transaction type (after column-name normalization).
# Based on the income / expenses / bank_transactions tables in data.sql.
REQUIRED_COLUMNS: dict[TransactionType, list[str]] = {
    TransactionType.INCOME: ["source", "amount", "date"],
    TransactionType.EXPENSE: ["category", "party_name", "amount", "date"],
    TransactionType.BANK_TRANSACTION: ["transaction_type", "amount", "date"],
}

# Columns that may be present but are not required.
OPTIONAL_COLUMNS: dict[TransactionType, list[str]] = {
    TransactionType.INCOME: ["description"],
    TransactionType.EXPENSE: ["description"],
    TransactionType.BANK_TRANSACTION: ["party_name", "description"],
}

# One column that is unique to each type; used to detect the type of a file.
DETECTION_COLUMNS: dict[TransactionType, str] = {
    TransactionType.INCOME: "source",
    TransactionType.EXPENSE: "category",
    TransactionType.BANK_TRANSACTION: "transaction_type",
}

# Accepted spellings of column names (applied after snake_case normalization,
# so "incomeDate", "Income Date" and "income_date" all become "date").
COLUMN_ALIASES: dict[str, str] = {
    "income_date": "date",
    "expense_date": "date",
    "transaction_date": "date",
    "party": "party_name",
}

# Text columns that are length-checked, with limits from data.sql (VARCHAR sizes).
TEXT_COLUMNS: dict[TransactionType, dict[str, int]] = {
    TransactionType.INCOME: {"source": 50},
    TransactionType.EXPENSE: {"category": 50, "party_name": 100},
    TransactionType.BANK_TRANSACTION: {"party_name": 100},
}

# Allowed values of the "transaction_type" column in bank transaction files
# (the INCOME/EXPENSE direction, per data.sql). Not the same thing as the
# TransactionType enum above, which is the kind of record being imported.
VALID_BANK_DIRECTIONS: list[str] = ["INCOME", "EXPENSE"]

# Accepted date formats. Day-first formats are used for slash/dot/dash dates
# (dd/mm/yyyy); month-first dates are intentionally NOT accepted (ambiguous).
DATE_FORMATS: list[str] = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%Y-%m-%d %H:%M:%S",  # what Excel date cells look like once read as text
]

# data.sql uses DECIMAL(12,2): at most 10 integer digits and 2 decimal places.
MAX_AMOUNT = Decimal("9999999999.99")
AMOUNT_PLACES = Decimal("0.01")

# --- FastAPI integration (see frontend/src/services/api.js) ----------------

# Same default as the frontend (VITE_API_BASE_URL). Override with this env var
# or the api_base_url option.
API_BASE_URL_ENV = "TAXSAINT_API_BASE_URL"
DEFAULT_API_BASE_URL = "http://localhost:8000"

# income / expenses match api.js. TODO: the bank transactions endpoint does not
# exist yet - confirm the path with the backend owner.
API_ENDPOINTS: dict[TransactionType, str] = {
    TransactionType.INCOME: "/api/financial/income",
    TransactionType.EXPENSE: "/api/financial/expenses",
    TransactionType.BANK_TRANSACTION: "/api/financial/bank-transactions",
}

# internal (normalized) column -> API field name. Income and expense names match
# the frontend forms (incomeDate, partyName, expenseDate...). Bank transaction
# names follow the same camelCase convention. TODO: confirm all names against
# the final FastAPI request schema (integration/api/schemas/requests.py).
API_FIELD_MAP: dict[TransactionType, dict[str, str]] = {
    TransactionType.INCOME: {
        "source": "source",
        "amount": "amount",
        "date": "incomeDate",
        "description": "description",
    },
    TransactionType.EXPENSE: {
        "party_name": "partyName",
        "category": "category",
        "amount": "amount",
        "date": "expenseDate",
        "description": "description",
    },
    TransactionType.BANK_TRANSACTION: {
        "party_name": "partyName",
        "transaction_type": "transactionType",
        "amount": "amount",
        "date": "transactionDate",
        "description": "description",
    },
}

# Field that carries the owning user on every record (data.sql: user_id NOT NULL).
API_USER_FIELD = "userId"

REQUEST_TIMEOUT_SECONDS = 10.0
CONNECT_RETRIES = 2          # retries only when the connection could not be made
CONNECT_BACKOFF_SECONDS = 0.3

# --- Duplicate-import ledger ------------------------------------------------

# Records successfully sent are remembered here so that accidentally importing
# the same file twice does not create the same records twice.
LEDGER_PATH_ENV = "TAXSAINT_IMPORT_LEDGER"
DEFAULT_LEDGER_PATH = Path.home() / ".taxsaint" / "import_ledger.json"

# --- Import status values ---------------------------------------------------

STATUS_SUCCESS = "success"                # everything valid was sent, nothing rejected
STATUS_PARTIAL = "partial"                # some records sent, some rejected/failed
STATUS_FAILED = "failed"                  # nothing was sent
STATUS_REJECTED = "rejected"              # file rejected before sending (columns/strict mode)
STATUS_NO_NEW_RECORDS = "no_new_records"  # every valid record was already imported
STATUS_DRY_RUN = "dry_run"                # validated only, nothing sent


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    """
    Describes one validation problem found in an input row.

    row_index is the row number as seen in the spreadsheet / CSV, where the
    header is row 1 (so the first data row is row 2). It is 0 for problems
    that concern the whole file (e.g. a missing column).
    """
    row_index: int
    column: Optional[str]
    message: str


@dataclass
class SendFailure:
    """One record the API did not accept, with the reason."""
    record: dict[str, Any]
    message: str


@dataclass
class SendResult:
    """Outcome of send_to_api()."""
    sent: list[dict[str, Any]] = field(default_factory=list)
    failed: list[SendFailure] = field(default_factory=list)
    not_attempted: list[dict[str, Any]] = field(default_factory=list)
    aborted_reason: Optional[str] = None


@dataclass
class ImportSummary:
    """Result of a full import run."""
    file_path: str
    transaction_type: Optional[TransactionType] = None
    user_id: Optional[int] = None
    status: str = STATUS_FAILED
    dry_run: bool = False
    total_rows: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    duplicate_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    errors: list[ValidationError] = field(default_factory=list)
    send_errors: list[str] = field(default_factory=list)
    rejected_file: Optional[str] = None
    message: str = ""


# ---------------------------------------------------------------------------
# 1. Reading (CSV-specific)
# ---------------------------------------------------------------------------

def read_csv_file(file_path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame of strings.

    Everything is read as text (no type guessing) so that validation sees
    exactly what was in the file. Blank lines are kept as empty rows so row
    numbers stay accurate; clean_dataframe() drops them later.

    Raises ImporterError if the file is missing, not a .csv, empty, or malformed.
    """
    path = Path(file_path)
    if not path.is_file():
        raise ImporterError(f"File not found: {path}")
    if path.suffix.lower() != ".csv":
        raise ImporterError(f"Not a .csv file: {path.name}")

    df: Optional[pd.DataFrame] = None
    # utf-8-sig handles Excel's "CSV UTF-8" BOM; latin-1 never fails to decode.
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
                na_values=[""],
                skip_blank_lines=False,
                encoding=encoding,
            )
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            raise ImporterError(f"The file is empty: {path.name}") from None
        except pd.errors.ParserError as exc:
            raise ImporterError(f"Could not parse {path.name}: {exc}") from None

    if df is None:
        raise ImporterError(f"Could not decode {path.name}; save it as UTF-8.")
    if df.empty:
        raise ImporterError(f"The file has a header but no data rows: {path.name}")
    return df


# ---------------------------------------------------------------------------
# 2. Cleaning + transaction type detection (shared)
# ---------------------------------------------------------------------------

def normalize_column_name(name: str) -> str:
    """
    Normalize a header to snake_case and apply COLUMN_ALIASES.

    "Party Name", "partyName" and "party_name" -> "party_name";
    "Income Date" / "incomeDate" -> "date".
    """
    text = str(name).strip()
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)   # camelCase -> camel_Case
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return COLUMN_ALIASES.get(text, text)


def _clean_cell(value: Any) -> Optional[str]:
    """Strip text; turn NaN / empty / whitespace-only cells into None."""
    if value is None:
        return None
    if not isinstance(value, str) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a freshly read DataFrame for validation.

    - normalizes column names (and rejects duplicates after normalization)
    - drops empty "Unnamed" columns (trailing commas / stray cells)
    - strips whitespace and turns blank cells into None
    - drops fully empty rows, KEEPING the original index so that row numbers
      in error messages still match the file

    Raises ImporterError if the result has no data rows.
    """
    cleaned = df.copy()
    columns = [normalize_column_name(c) for c in cleaned.columns]
    duplicates = sorted({c for c in columns if columns.count(c) > 1})
    if duplicates:
        raise ImporterError(
            "Duplicate column names (after normalization): " + ", ".join(duplicates)
        )
    cleaned.columns = columns

    stray = [c for c in cleaned.columns if c.startswith("unnamed") and cleaned[c].isna().all()]
    cleaned = cleaned.drop(columns=stray)

    cleaned = cleaned.astype(object).apply(lambda col: col.map(_clean_cell))
    cleaned = cleaned.dropna(how="all")
    if cleaned.empty:
        raise ImporterError("The file contains no data rows.")
    return cleaned


def detect_transaction_type(df: pd.DataFrame) -> TransactionType:
    """
    Decide whether the data is income, expense, or bank transactions.

    Looks for the column unique to each type: "source" -> income,
    "category" -> expense, "transaction_type" -> bank transaction.
    Expects normalized column names (see clean_dataframe()).

    Raises ImporterError if no type, or more than one type, matches.
    """
    matches = [t for t, column in DETECTION_COLUMNS.items() if column in df.columns]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ImporterError(
            "Could not detect the transaction type. Expected one of the columns: "
            + ", ".join(f"'{c}' ({t.value})" for t, c in DETECTION_COLUMNS.items())
            + ". You can also specify the type explicitly."
        )
    raise ImporterError(
        "The file matches more than one transaction type ("
        + ", ".join(t.value for t in matches)
        + "). Specify the type explicitly."
    )


# ---------------------------------------------------------------------------
# 3. Column validation (shared)
# ---------------------------------------------------------------------------

def validate_columns(
    df: pd.DataFrame,
    transaction_type: TransactionType,
) -> list[str]:
    """Return the required columns that are missing (empty list = OK)."""
    return [c for c in REQUIRED_COLUMNS[transaction_type] if c not in df.columns]


# ---------------------------------------------------------------------------
# 4. Row validation (shared)
# ---------------------------------------------------------------------------

def parse_amount(raw: Any) -> Decimal:
    """
    Parse an amount like "1500", "1,234.50" or "₹ 2,000" into a Decimal.

    Raises ValueError (with a user-readable message) if it is not a positive,
    finite number with at most 2 decimal places that fits DECIMAL(12,2).
    """
    text = str(raw).strip()
    text = re.sub(r"^(?:₹|rs\.?|inr|\$)\s*", "", text, flags=re.IGNORECASE)
    text = text.replace(",", "").replace(" ", "")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"Amount '{raw}' is not a valid number") from None
    if not value.is_finite():
        raise ValueError(f"Amount '{raw}' is not a valid number")
    if value <= 0:
        raise ValueError("Amount must be greater than zero")
    if value > MAX_AMOUNT:
        raise ValueError(f"Amount is too large (maximum {MAX_AMOUNT})")
    if value != value.quantize(AMOUNT_PLACES):
        raise ValueError("Amount has more than 2 decimal places")
    return value.quantize(AMOUNT_PLACES)


def parse_date(raw: Any) -> date:
    """
    Parse a date using DATE_FORMATS.

    Raises ValueError if the format is not supported or the date is in the future.
    """
    text = str(raw).strip()
    parsed: Optional[date] = None
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt).date()
            break
        except ValueError:
            continue
    if parsed is None:
        raise ValueError(
            f"Date '{raw}' is not in a supported format (use YYYY-MM-DD or DD/MM/YYYY)"
        )
    if parsed > date.today():
        raise ValueError(f"Date '{raw}' is in the future")
    return parsed


def _get(row: pd.Series, column: str) -> Optional[str]:
    """Return a cell as stripped text, or None if the column/cell is missing."""
    if column not in row.index:
        return None
    return _clean_cell(row[column])


def _row_number(index: Any) -> int:
    """Convert a DataFrame index to the row number shown in the file (header = row 1)."""
    return int(index) + 2


def validate_row(
    row: pd.Series,
    row_index: int,
    transaction_type: TransactionType,
) -> list[ValidationError]:
    """
    Validate a single row (row_index is the file row number, header = row 1).

    Checks: missing required values, amount, date, text length limits, and
    (for bank transactions) the INCOME/EXPENSE direction.
    Returns the list of problems (empty list = row is valid).
    """
    errors: list[ValidationError] = []

    def add(column: Optional[str], message: str) -> None:
        errors.append(ValidationError(row_index, column, message))

    for column in REQUIRED_COLUMNS[transaction_type]:
        if _get(row, column) is None:
            add(column, "Missing value")

    for column, limit in TEXT_COLUMNS[transaction_type].items():
        value = _get(row, column)
        if value is not None and len(value) > limit:
            add(column, f"Too long ({len(value)} characters, maximum {limit})")

    amount = _get(row, "amount")
    if amount is not None:
        try:
            parse_amount(amount)
        except ValueError as exc:
            add("amount", str(exc))

    raw_date = _get(row, "date")
    if raw_date is not None:
        try:
            parse_date(raw_date)
        except ValueError as exc:
            add("date", str(exc))

    if transaction_type is TransactionType.BANK_TRANSACTION:
        direction = _get(row, "transaction_type")
        if direction is not None and direction.upper() not in VALID_BANK_DIRECTIONS:
            add(
                "transaction_type",
                f"Invalid value '{direction}' (must be one of: "
                + ", ".join(VALID_BANK_DIRECTIONS) + ")",
            )

    return errors


# ---------------------------------------------------------------------------
# 5. Separating valid and invalid rows (shared)
# ---------------------------------------------------------------------------

def split_valid_invalid(
    df: pd.DataFrame,
    transaction_type: TransactionType,
) -> tuple[pd.DataFrame, pd.DataFrame, list[ValidationError]]:
    """
    Validate every row and split the results.

    Returns (valid_rows_df, invalid_rows_df, all_validation_errors).
    The invalid DataFrame has an extra "validation_errors" column describing
    what is wrong with each row.
    """
    all_errors: list[ValidationError] = []
    valid_index: list[Any] = []
    invalid_index: list[Any] = []
    invalid_messages: list[str] = []

    for index, row in df.iterrows():
        row_errors = validate_row(row, _row_number(index), transaction_type)
        if row_errors:
            all_errors.extend(row_errors)
            invalid_index.append(index)
            invalid_messages.append("; ".join(f"{e.column}: {e.message}" for e in row_errors))
        else:
            valid_index.append(index)

    valid_df = df.loc[valid_index].copy()
    invalid_df = df.loc[invalid_index].copy()
    invalid_df["validation_errors"] = invalid_messages
    return valid_df, invalid_df, all_errors


def export_rejected_rows(invalid_df: pd.DataFrame, output_path: str | Path) -> Path:
    """
    Write rejected rows to a CSV so they can be fixed and re-imported.

    Adds a "source_row" column with the row number in the original file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    output = invalid_df.copy()
    output.insert(0, "source_row", [_row_number(i) for i in output.index])
    output.to_csv(path, index=False, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 6. Conversion to TaxSaint internal format (shared)
# ---------------------------------------------------------------------------

def convert_to_internal_format(
    valid_df: pd.DataFrame,
    transaction_type: TransactionType,
    user_id: int,
) -> list[dict[str, Any]]:
    """
    Convert validated rows into the JSON payloads the FastAPI backend expects.

    Field names come from API_FIELD_MAP (TODO: confirm against the final
    backend schema). Amounts are numbers rounded to 2 decimals, dates are
    ISO "YYYY-MM-DD", and every record carries the owning user's id.
    Optional columns that are empty are left out of the payload.
    """
    mapping = API_FIELD_MAP[transaction_type]
    records: list[dict[str, Any]] = []

    for _, row in valid_df.iterrows():
        record: dict[str, Any] = {API_USER_FIELD: user_id}
        for column, api_field in mapping.items():
            value = _get(row, column)
            if value is None:
                continue
            if column == "amount":
                record[api_field] = float(parse_amount(value))
            elif column == "date":
                record[api_field] = parse_date(value).isoformat()
            elif column == "transaction_type":
                record[api_field] = value.upper()
            else:
                record[api_field] = value
        records.append(record)
    return records


# ---------------------------------------------------------------------------
# 7. Sending to FastAPI (shared)
# ---------------------------------------------------------------------------

def _resolve_base_url(api_base_url: Optional[str]) -> str:
    return (api_base_url or os.environ.get(API_BASE_URL_ENV) or DEFAULT_API_BASE_URL).rstrip("/")


def _describe_http_error(response: requests.Response) -> str:
    """Build a short, readable message from a non-2xx FastAPI response."""
    detail: Any
    try:
        payload = response.json()
        detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
    except ValueError:
        detail = response.text
    return f"HTTP {response.status_code}: {str(detail)[:300]}"


def send_to_api(
    records: list[dict[str, Any]],
    transaction_type: TransactionType,
    api_base_url: Optional[str] = None,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> SendResult:
    """
    POST records to the FastAPI backend, one request per record.

    The frontend's API client posts single records to /api/financial/income
    and /api/financial/expenses, so the importer uses the same endpoints.
    TODO: if the backend adds a bulk endpoint, switch to it here.

    - Records the API accepts (2xx) go in SendResult.sent.
    - Records it rejects (e.g. 422) go in SendResult.failed with the reason;
      the remaining records are still attempted.
    - If the API cannot be reached (or a request times out) sending stops:
      the remaining records are returned in not_attempted and aborted_reason
      is set. Retries happen only when a connection could not be made at all,
      so a record is never POSTed twice.

    Never talks to Supabase; no credentials are involved.
    """
    url = _resolve_base_url(api_base_url) + API_ENDPOINTS[transaction_type]
    result = SendResult()

    retry = Retry(
        total=None, connect=CONNECT_RETRIES, read=0, status=0, other=0, redirect=0,
        backoff_factor=CONNECT_BACKOFF_SECONDS,
    )
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))

    try:
        for position, record in enumerate(records):
            try:
                response = session.post(url, json=record, timeout=timeout)
            except (requests.ConnectionError, requests.Timeout) as exc:
                result.failed.append(
                    SendFailure(record, f"Connection problem: {exc.__class__.__name__}")
                )
                result.not_attempted = list(records[position + 1:])
                result.aborted_reason = f"Could not reach the API at {url} ({exc.__class__.__name__})"
                break
            except requests.RequestException as exc:
                result.failed.append(SendFailure(record, f"Request error: {exc}"))
                continue

            if 200 <= response.status_code < 300:
                result.sent.append(record)
            else:
                result.failed.append(SendFailure(record, _describe_http_error(response)))
    finally:
        session.close()

    return result


# ---------------------------------------------------------------------------
# 8. Duplicate handling (shared)
# ---------------------------------------------------------------------------

def _fingerprint(record: dict[str, Any], transaction_type: TransactionType) -> str:
    """Stable hash of a record's identifying fields (the description is ignored)."""
    fields = [
        record.get(api_field)
        for api_field in API_FIELD_MAP[transaction_type].values()
        if api_field != "description"
    ]
    payload = json.dumps(
        [transaction_type.value, record.get(API_USER_FIELD), fields], sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ledger_path(ledger_path: Optional[str | Path]) -> Path:
    if ledger_path:
        return Path(ledger_path)
    env_value = os.environ.get(LEDGER_PATH_ENV)
    return Path(env_value) if env_value else DEFAULT_LEDGER_PATH


def _load_ledger(path: Path) -> dict[str, int]:
    """Load {fingerprint: times_imported}. A missing ledger is an empty one."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        counts = data["counts"]
        return {str(k): int(v) for k, v in counts.items()}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ImporterError(
            f"The import history file is unreadable: {path} ({exc}). "
            "Fix or delete it to continue."
        ) from None


def _save_ledger(path: Path, counts: dict[str, int]) -> None:
    """Write the ledger atomically (temp file + replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as temp_file:
            json.dump({"version": 1, "counts": counts}, temp_file)
        os.replace(temp_name, path)
    except BaseException:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def handle_duplicates(
    records: list[dict[str, Any]],
    transaction_type: TransactionType,
    ledger_path: Optional[str | Path] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Split records into (unique, duplicates) using the local import history.

    A record is a duplicate if an identical one (same user, type, amounts,
    dates, names) was already sent by an earlier import. Counts are tracked,
    so if a file legitimately contains the same row twice and was imported
    once, re-importing it marks both rows as duplicates.

    Repeated rows WITHIN one new file are deliberately kept: spotting
    suspicious repeated expenses is the fraud engine's job, not the importer's.
    """
    remaining = dict(_load_ledger(_ledger_path(ledger_path)))
    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for record in records:
        fingerprint = _fingerprint(record, transaction_type)
        if remaining.get(fingerprint, 0) > 0:
            remaining[fingerprint] -= 1
            duplicates.append(record)
        else:
            unique.append(record)
    return unique, duplicates


def record_imported(
    records: list[dict[str, Any]],
    transaction_type: TransactionType,
    ledger_path: Optional[str | Path] = None,
) -> None:
    """Remember successfully sent records so a later re-import is caught."""
    if not records:
        return
    path = _ledger_path(ledger_path)
    counts = _load_ledger(path)
    for record in records:
        fingerprint = _fingerprint(record, transaction_type)
        counts[fingerprint] = counts.get(fingerprint, 0) + 1
    _save_ledger(path, counts)


# ---------------------------------------------------------------------------
# 9. Shared pipeline + CSV orchestration
# ---------------------------------------------------------------------------

def _validate_user_id(user_id: Any) -> int:
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ImporterError("user_id must be a positive integer.")
    return user_id


def process_dataframe(
    df: pd.DataFrame,
    source_path: str | Path,
    user_id: int,
    *,
    forced_type: Optional[TransactionType] = None,
    dry_run: bool = False,
    strict: bool = False,
    check_duplicates: bool = True,
    api_base_url: Optional[str] = None,
    ledger_path: Optional[str | Path] = None,
    rejected_out: Optional[str | Path] = None,
) -> ImportSummary:
    """
    Run everything AFTER reading; shared by the CSV and Excel importers.

    Options:
        forced_type       skip type detection and use this type.
        dry_run           validate and convert, but send nothing and record nothing.
        strict            if ANY row is invalid, send nothing (all-or-nothing).
        check_duplicates  skip records already imported earlier (default on).
        api_base_url      override the FastAPI base URL.
        ledger_path       override where import history is kept.
        rejected_out      write rejected rows to this CSV for fixing.

    File-level problems raise ImporterError. Row-level problems never raise;
    they are reported in the returned ImportSummary.
    """
    _validate_user_id(user_id)
    summary = ImportSummary(file_path=str(source_path), user_id=user_id, dry_run=dry_run)

    df = clean_dataframe(df)
    summary.total_rows = len(df)

    transaction_type = forced_type or detect_transaction_type(df)
    summary.transaction_type = transaction_type

    missing = validate_columns(df, transaction_type)
    if missing:
        summary.errors = [ValidationError(0, c, "Required column is missing") for c in missing]
        summary.invalid_count = summary.total_rows
        summary.status = STATUS_REJECTED
        summary.message = "Missing required column(s): " + ", ".join(missing)
        return summary

    valid_df, invalid_df, errors = split_valid_invalid(df, transaction_type)
    summary.valid_count = len(valid_df)
    summary.invalid_count = len(invalid_df)
    summary.errors = errors

    if rejected_out and not invalid_df.empty:
        summary.rejected_file = str(export_rejected_rows(invalid_df, rejected_out))

    if strict and summary.invalid_count:
        summary.status = STATUS_REJECTED
        summary.message = (
            f"Strict mode: {summary.invalid_count} invalid row(s) found, nothing was sent."
        )
        return summary

    records = convert_to_internal_format(valid_df, transaction_type, user_id)

    if check_duplicates:
        records, duplicates = handle_duplicates(records, transaction_type, ledger_path)
        summary.duplicate_count = len(duplicates)

    if dry_run:
        summary.status = STATUS_DRY_RUN
        summary.message = (
            f"Dry run: {len(records)} record(s) would be sent, "
            f"{summary.duplicate_count} duplicate(s) skipped, "
            f"{summary.invalid_count} row(s) rejected."
        )
        return summary

    if not records:
        if summary.valid_count == 0:
            summary.status = STATUS_FAILED
            summary.message = "No valid rows to import."
        else:
            summary.status = STATUS_NO_NEW_RECORDS
            summary.message = "All valid rows were already imported earlier."
        return summary

    result = send_to_api(records, transaction_type, api_base_url=api_base_url)
    record_imported(result.sent, transaction_type, ledger_path)

    summary.sent_count = len(result.sent)
    summary.failed_count = len(result.failed) + len(result.not_attempted)
    summary.send_errors = [
        f"{json.dumps(f.record, sort_keys=True)} -> {f.message}" for f in result.failed
    ]

    if summary.sent_count == 0:
        summary.status = STATUS_FAILED
    elif summary.invalid_count or summary.failed_count:
        summary.status = STATUS_PARTIAL
    else:
        summary.status = STATUS_SUCCESS

    parts = [f"Sent {summary.sent_count} of {len(records)} record(s)."]
    if result.aborted_reason:
        parts.append(f"Stopped early: {result.aborted_reason}.")
    summary.message = " ".join(parts)
    return summary


def import_csv(file_path: str | Path, user_id: int, **options: Any) -> ImportSummary:
    """
    Run the full import workflow for one CSV file.

    options are passed to process_dataframe() (forced_type, dry_run, strict,
    check_duplicates, api_base_url, ledger_path, rejected_out).
    Raises ImporterError for file-level problems.
    """
    df = read_csv_file(file_path)
    return process_dataframe(df, file_path, user_id, **options)


# ---------------------------------------------------------------------------
# Command-line interface (shared with excel_importer.py)
# ---------------------------------------------------------------------------

def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the command-line options shared by the CSV and Excel importers."""
    parser.add_argument("--user-id", type=int,
                        help="ID of the TaxSaint user the records belong to (required)")
    parser.add_argument("--type", dest="forced_type",
                        choices=[t.value for t in TransactionType],
                        help="transaction type (default: detect from the columns)")
    parser.add_argument("--dry-run", action="store_true",
                        help="validate only; send nothing")
    parser.add_argument("--strict", action="store_true",
                        help="send nothing if any row is invalid")
    parser.add_argument("--no-duplicate-check", action="store_true",
                        help="do not skip records that were imported before")
    parser.add_argument("--rejected-out", metavar="PATH",
                        help="write rejected rows to this CSV file")
    parser.add_argument("--api-url", metavar="URL",
                        help=f"FastAPI base URL (default: ${API_BASE_URL_ENV} or {DEFAULT_API_BASE_URL})")
    parser.add_argument("--ledger", metavar="PATH",
                        help="where to keep the import history")


def options_from_args(args: argparse.Namespace) -> dict[str, Any]:
    """Convert parsed command-line arguments into process_dataframe() options."""
    return {
        "forced_type": TransactionType(args.forced_type) if args.forced_type else None,
        "dry_run": args.dry_run,
        "strict": args.strict,
        "check_duplicates": not args.no_duplicate_check,
        "api_base_url": args.api_url,
        "ledger_path": args.ledger,
        "rejected_out": args.rejected_out,
    }


def print_summary(summary: ImportSummary, max_errors: int = 20) -> None:
    """Print a human-readable import summary."""
    kind = summary.transaction_type.value if summary.transaction_type else "unknown"
    print(f"File:        {summary.file_path}")
    print(f"Type:        {kind}")
    print(f"User ID:     {summary.user_id}")
    print(f"Status:      {summary.status.upper()}")
    print(f"Rows read:   {summary.total_rows}")
    print(f"Valid:       {summary.valid_count}")
    print(f"Rejected:    {summary.invalid_count}")
    print(f"Duplicates:  {summary.duplicate_count}")
    print(f"Sent:        {summary.sent_count}")
    print(f"Send failed: {summary.failed_count}")
    if summary.rejected_file:
        print(f"Rejected rows written to: {summary.rejected_file}")
    if summary.message:
        print(summary.message)
    for error in summary.errors[:max_errors]:
        where = f"row {error.row_index}" if error.row_index else "file"
        column = f", {error.column}" if error.column else ""
        print(f"  [{where}{column}] {error.message}")
    if len(summary.errors) > max_errors:
        print(f"  ... and {len(summary.errors) - max_errors} more validation error(s)")
    for message in summary.send_errors[:max_errors]:
        print(f"  [send] {message}")


def exit_code_for(summary: ImportSummary) -> int:
    """0 = fine, 1 = problems reported in the summary."""
    if summary.status == STATUS_DRY_RUN:
        return 1 if summary.invalid_count else 0
    return 0 if summary.status in (STATUS_SUCCESS, STATUS_NO_NEW_RECORDS) else 1


def main(argv: Optional[list[str]] = None) -> int:
    """Command-line entry point for CSV files. Returns the process exit code."""
    parser = argparse.ArgumentParser(description="Import a CSV of income, expense or bank transactions into TaxSaint.")
    parser.add_argument("file", help="path to the .csv file")
    add_common_arguments(parser)
    args = parser.parse_args(argv)
    if args.user_id is None:
        parser.error("--user-id is required")

    try:
        summary = import_csv(args.file, args.user_id, **options_from_args(args))
    except ImporterError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 2
    print_summary(summary)
    return exit_code_for(summary)


if __name__ == "__main__":
    sys.exit(main())
