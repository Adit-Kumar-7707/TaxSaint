"""
Tests for data_input/importers (csv_importer.py and excel_importer.py).

Run from the project root:
    pip install -r requirements.txt pytest
    python -m pytest tests/data_input -v

No real backend or database is needed: a tiny local HTTP server stands in for
the FastAPI endpoints and records what the importer sends.
"""

import json
import socket
import sys
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data_input.importers import csv_importer as ci          # noqa: E402
from data_input.importers import excel_importer as ei        # noqa: E402
from data_input.importers.csv_importer import (               # noqa: E402
    ImporterError,
    TransactionType as T,
)

SAMPLES = PROJECT_ROOT / "data_input" / "sample_data"
USER_ID = 7


# ---------------------------------------------------------------------------
# Mock FastAPI backend
# ---------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        server = self.server
        server.received.append((self.path, body))
        # Reject any record whose party/source/category is "REJECT-ME".
        if "REJECT-ME" in body.values():
            self.send_response(422)
            payload = {"detail": "rejected by mock"}
        else:
            self.send_response(201)
            payload = {"ok": True}
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *args):  # keep test output quiet
        pass


@pytest.fixture
def api():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.received = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.url = f"http://127.0.0.1:{server.server_address[1]}"
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def opts(tmp_path, api):
    """Options that point the importer at the mock API and a throwaway ledger."""
    return {"api_base_url": api.url, "ledger_path": tmp_path / "ledger.json"}


def write_csv(tmp_path, text, name="data.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def free_port_url():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return f"http://127.0.0.1:{port}"


# ---------------------------------------------------------------------------
# Reading + cleaning
# ---------------------------------------------------------------------------

def test_read_csv_keeps_text_and_blank_lines(tmp_path):
    path = write_csv(tmp_path, "source,amount,date\nSalary,1000,2026-01-01\n\nBonus,500,2026-01-02\n")
    df = ci.read_csv_file(path)
    assert list(df.columns) == ["source", "amount", "date"]
    assert len(df) == 3  # blank line kept so row numbers stay correct


@pytest.mark.parametrize("content, message", [
    ("", "empty"),
    ("source,amount,date\n", "no data rows"),
])
def test_read_csv_rejects_empty(tmp_path, content, message):
    with pytest.raises(ImporterError, match=message):
        ci.read_csv_file(write_csv(tmp_path, content))


def test_read_csv_rejects_missing_and_wrong_extension(tmp_path):
    with pytest.raises(ImporterError, match="not found"):
        ci.read_csv_file(tmp_path / "nope.csv")
    other = tmp_path / "data.txt"
    other.write_text("a,b\n1,2\n")
    with pytest.raises(ImporterError, match="Not a .csv"):
        ci.read_csv_file(other)


def test_read_csv_handles_bom_and_latin1(tmp_path):
    bom = tmp_path / "bom.csv"
    bom.write_bytes("\ufeffsource,amount,date\nSalary,1,2026-01-01\n".encode("utf-8"))
    assert list(ci.read_csv_file(bom).columns)[0] == "source"
    latin = tmp_path / "latin.csv"
    latin.write_bytes("source,amount,date\nCaf\xe9,1,2026-01-01\n".encode("latin-1"))
    assert ci.read_csv_file(latin).iloc[0]["source"] == "Café"


def test_clean_dataframe_normalizes_headers_and_drops_blank_rows():
    df = pd.DataFrame({"Party Name": [" A ", None, "B"], "incomeDate": ["x", None, "y"], "Unnamed: 2": [None] * 3})
    cleaned = ci.clean_dataframe(df)
    assert list(cleaned.columns) == ["party_name", "date"]
    assert list(cleaned.index) == [0, 2]            # original index kept
    assert cleaned.loc[0, "party_name"] == "A"      # stripped


def test_clean_dataframe_rejects_duplicate_columns():
    df = pd.DataFrame([["1", "2"]], columns=["date", "Income Date"])
    with pytest.raises(ImporterError, match="Duplicate column"):
        ci.clean_dataframe(df)


# ---------------------------------------------------------------------------
# Detection + column validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("columns, expected", [
    (["source", "amount", "date"], T.INCOME),
    (["category", "party_name", "amount", "date"], T.EXPENSE),
    (["party_name", "transaction_type", "amount", "date"], T.BANK_TRANSACTION),
])
def test_detect_transaction_type(columns, expected):
    assert ci.detect_transaction_type(pd.DataFrame(columns=columns)) is expected


def test_detect_transaction_type_unknown_and_ambiguous():
    with pytest.raises(ImporterError, match="Could not detect"):
        ci.detect_transaction_type(pd.DataFrame(columns=["amount", "date"]))
    with pytest.raises(ImporterError, match="more than one"):
        ci.detect_transaction_type(pd.DataFrame(columns=["source", "category"]))


def test_validate_columns_reports_missing():
    df = pd.DataFrame(columns=["category", "amount"])
    assert ci.validate_columns(df, T.EXPENSE) == ["party_name", "date"]
    assert ci.validate_columns(pd.DataFrame(columns=["source", "amount", "date"]), T.INCOME) == []


# ---------------------------------------------------------------------------
# Parsing + row validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("1500", "1500.00"), ("1,234.50", "1234.50"), ("₹ 2,000", "2000.00"),
    ("Rs. 99.9", "99.90"), (" 10 ", "10.00"),
])
def test_parse_amount_valid(raw, expected):
    assert str(ci.parse_amount(raw)) == expected


@pytest.mark.parametrize("raw", ["abc", "0", "-5", "12.345", "NaN", "inf", "99999999999.00", ""])
def test_parse_amount_invalid(raw):
    with pytest.raises(ValueError):
        ci.parse_amount(raw)


@pytest.mark.parametrize("raw, expected", [
    ("2026-04-30", date(2026, 4, 30)), ("30/04/2026", date(2026, 4, 30)),
    ("30-04-2026", date(2026, 4, 30)), ("2026/04/30", date(2026, 4, 30)),
    ("30.04.2026", date(2026, 4, 30)), ("2026-04-30 00:00:00", date(2026, 4, 30)),
])
def test_parse_date_valid(raw, expected):
    assert ci.parse_date(raw) == expected


def test_parse_date_invalid_and_future():
    for raw in ["not a date", "2026-13-40", "04/30/2026"]:
        with pytest.raises(ValueError, match="supported format"):
            ci.parse_date(raw)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValueError, match="future"):
        ci.parse_date(tomorrow)


def _row(**values):
    return pd.Series(values, dtype=object)


@pytest.mark.parametrize("ttype, row, column", [
    (T.INCOME, dict(source=None, amount="10", date="2026-01-01"), "source"),
    (T.INCOME, dict(source="Salary", amount="-1", date="2026-01-01"), "amount"),
    (T.INCOME, dict(source="Salary", amount="10", date="31/31/2026"), "date"),
    (T.INCOME, dict(source="x" * 51, amount="10", date="2026-01-01"), "source"),
    (T.EXPENSE, dict(category="Rent", party_name=None, amount="10", date="2026-01-01"), "party_name"),
    (T.EXPENSE, dict(category="Rent", party_name="A", amount="1.234", date="2026-01-01"), "amount"),
    (T.BANK_TRANSACTION, dict(transaction_type="REFUND", amount="10", date="2026-01-01"), "transaction_type"),
    (T.BANK_TRANSACTION, dict(transaction_type="INCOME", party_name="x" * 101, amount="10", date="2026-01-01"), "party_name"),
])
def test_validate_row_flags_problem(ttype, row, column):
    errors = ci.validate_row(_row(**row), 5, ttype)
    assert [e.column for e in errors] == [column]
    assert errors[0].row_index == 5


def test_validate_row_accepts_good_rows_and_optional_bank_party():
    assert ci.validate_row(_row(source="Salary", amount="10", date="2026-01-01"), 2, T.INCOME) == []
    bank = _row(transaction_type="income", amount="10", date="2026-01-01")  # lower-case ok, no party
    assert ci.validate_row(bank, 2, T.BANK_TRANSACTION) == []


def test_split_valid_invalid_uses_file_row_numbers(tmp_path):
    df = ci.clean_dataframe(ci.read_csv_file(write_csv(
        tmp_path,
        "source,amount,date\nSalary,1000,2026-01-01\nBonus,abc,2026-01-02\n,5,2026-01-03\n",
    )))
    valid, invalid, errors = ci.split_valid_invalid(df, T.INCOME)
    assert len(valid) == 1 and len(invalid) == 2
    assert [(e.row_index, e.column) for e in errors] == [(3, "amount"), (4, "source")]
    assert "amount" in invalid.iloc[0]["validation_errors"]


# ---------------------------------------------------------------------------
# Conversion to the API format
# ---------------------------------------------------------------------------

def test_convert_income_matches_frontend_field_names():
    df = ci.clean_dataframe(pd.DataFrame({"source": ["Salary"], "amount": ["1,000.5"], "date": ["30/04/2026"],
                                          "description": ["April"]}))
    assert ci.convert_to_internal_format(df, T.INCOME, USER_ID) == [{
        "userId": USER_ID, "source": "Salary", "amount": 1000.5,
        "incomeDate": "2026-04-30", "description": "April",
    }]


def test_convert_expense_and_bank_and_skips_empty_optional():
    expense = ci.clean_dataframe(pd.DataFrame({"category": ["Rent"], "party_name": ["Sharma"],
                                               "amount": ["18000"], "date": ["2026-05-01"]}))
    assert ci.convert_to_internal_format(expense, T.EXPENSE, USER_ID)[0] == {
        "userId": USER_ID, "partyName": "Sharma", "category": "Rent",
        "amount": 18000.0, "expenseDate": "2026-05-01",
    }
    bank = ci.clean_dataframe(pd.DataFrame({"transaction_type": ["income"], "amount": ["5"],
                                            "date": ["2026-05-01"], "party_name": [None]}))
    assert ci.convert_to_internal_format(bank, T.BANK_TRANSACTION, USER_ID)[0] == {
        "userId": USER_ID, "transactionType": "INCOME", "amount": 5.0, "transactionDate": "2026-05-01",
    }


# ---------------------------------------------------------------------------
# Full imports against the mock API
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name, endpoint, count", [
    ("income.csv", "/api/financial/income", 3),
    ("expense.csv", "/api/financial/expenses", 3),
    ("bank_transactions.csv", "/api/financial/bank-transactions", 3),
])
def test_sample_files_import_end_to_end(api, opts, name, endpoint, count):
    summary = ci.import_csv(SAMPLES / name, USER_ID, **opts)
    assert summary.status == ci.STATUS_SUCCESS
    assert (summary.valid_count, summary.sent_count, summary.invalid_count) == (count, count, 0)
    assert len(api.received) == count
    assert all(path == endpoint and body["userId"] == USER_ID for path, body in api.received)


def test_reimporting_same_file_is_caught_as_duplicates(api, opts):
    ci.import_csv(SAMPLES / "income.csv", USER_ID, **opts)
    api.received.clear()
    again = ci.import_csv(SAMPLES / "income.csv", USER_ID, **opts)
    assert again.status == ci.STATUS_NO_NEW_RECORDS
    assert again.duplicate_count == 3 and api.received == []
    # a different user is not affected by the first user's history
    other = ci.import_csv(SAMPLES / "income.csv", USER_ID + 1, **opts)
    assert other.status == ci.STATUS_SUCCESS


def test_duplicate_check_can_be_disabled(api, opts):
    ci.import_csv(SAMPLES / "income.csv", USER_ID, **opts)
    again = ci.import_csv(SAMPLES / "income.csv", USER_ID, check_duplicates=False, **opts)
    assert again.status == ci.STATUS_SUCCESS and again.sent_count == 3


def test_repeated_rows_within_one_file_are_kept(api, opts, tmp_path):
    path = write_csv(tmp_path, "category,party_name,amount,date\n"
                               "Travel,IndiGo,500,2026-06-01\nTravel,IndiGo,500,2026-06-01\n")
    summary = ci.import_csv(path, USER_ID, **opts)
    assert summary.sent_count == 2 and summary.duplicate_count == 0   # fraud engine's job
    again = ci.import_csv(path, USER_ID, **opts)
    assert again.duplicate_count == 2 and again.status == ci.STATUS_NO_NEW_RECORDS


def test_partial_import_sends_valid_rows_and_reports_invalid(api, opts, tmp_path):
    path = write_csv(tmp_path, "source,amount,date\nSalary,1000,2026-01-01\nBonus,oops,2026-01-02\n")
    rejected = tmp_path / "out" / "rejected.csv"
    summary = ci.import_csv(path, USER_ID, rejected_out=rejected, **opts)
    assert summary.status == ci.STATUS_PARTIAL
    assert (summary.sent_count, summary.invalid_count) == (1, 1)
    assert summary.rejected_file == str(rejected)
    saved = pd.read_csv(rejected)
    assert list(saved["source_row"]) == [3] and "amount" in saved.loc[0, "validation_errors"]


def test_strict_mode_sends_nothing_if_any_row_invalid(api, opts, tmp_path):
    path = write_csv(tmp_path, "source,amount,date\nSalary,1000,2026-01-01\nBonus,oops,2026-01-02\n")
    summary = ci.import_csv(path, USER_ID, strict=True, **opts)
    assert summary.status == ci.STATUS_REJECTED and api.received == []


def test_missing_columns_are_rejected_with_summary(api, opts, tmp_path):
    path = write_csv(tmp_path, "category,amount\nRent,10\n")
    summary = ci.import_csv(path, USER_ID, **opts)
    assert summary.status == ci.STATUS_REJECTED and api.received == []
    assert {e.column for e in summary.errors} == {"party_name", "date"}


def test_forced_type_overrides_detection(api, opts, tmp_path):
    path = write_csv(tmp_path, "amount,date,source\n10,2026-01-01,Salary\n")
    summary = ci.import_csv(path, USER_ID, forced_type=T.INCOME, **opts)
    assert summary.transaction_type is T.INCOME and summary.status == ci.STATUS_SUCCESS


def test_dry_run_sends_and_records_nothing(api, opts):
    summary = ci.import_csv(SAMPLES / "expense.csv", USER_ID, dry_run=True, **opts)
    assert summary.status == ci.STATUS_DRY_RUN and api.received == []
    assert not opts["ledger_path"].exists()
    assert ci.import_csv(SAMPLES / "expense.csv", USER_ID, **opts).status == ci.STATUS_SUCCESS


def test_api_rejection_is_reported_and_not_remembered(api, opts, tmp_path):
    path = write_csv(tmp_path, "source,amount,date\nSalary,1000,2026-01-01\nREJECT-ME,5,2026-01-02\n")
    summary = ci.import_csv(path, USER_ID, **opts)
    assert summary.status == ci.STATUS_PARTIAL and summary.sent_count == 1 and summary.failed_count == 1
    assert "422" in summary.send_errors[0] and "rejected by mock" in summary.send_errors[0]
    # only the accepted record is in the history, so the failed one can be retried
    retry = ci.import_csv(path, USER_ID, **opts)
    assert retry.duplicate_count == 1 and len(api.received) == 3


def test_unreachable_api_aborts_cleanly(opts, tmp_path):
    opts = {**opts, "api_base_url": free_port_url()}
    summary = ci.import_csv(SAMPLES / "income.csv", USER_ID, **opts)
    assert summary.status == ci.STATUS_FAILED and summary.sent_count == 0
    assert summary.failed_count == 3 and "Could not reach" in summary.message
    assert not opts["ledger_path"].exists()


def test_invalid_user_id_and_corrupt_ledger(api, opts, tmp_path):
    for bad in (0, -1, "1", True):
        with pytest.raises(ImporterError, match="user_id"):
            ci.import_csv(SAMPLES / "income.csv", bad, **opts)
    opts["ledger_path"].write_text("{not json")
    with pytest.raises(ImporterError, match="import history"):
        ci.import_csv(SAMPLES / "income.csv", USER_ID, **opts)


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

def make_workbook(path, sheets):
    with pd.ExcelWriter(path) as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    return path


def test_excel_import_with_real_date_cells_and_named_sheet(api, opts, tmp_path):
    book = make_workbook(tmp_path / "book.xlsx", {
        "Notes": pd.DataFrame({"x": [1]}),
        "Income": pd.DataFrame({"Source": ["Salary", "Freelance"], "Amount": [85000, 12000.5],
                                "Date": [datetime(2026, 4, 30), datetime(2026, 6, 15)]}),
    })
    assert ei.list_sheets(book) == ["Notes", "Income"]
    summary = ei.import_excel(book, USER_ID, "Income", **opts)
    assert summary.status == ci.STATUS_SUCCESS and summary.sent_count == 2
    assert api.received[0][1] == {"userId": USER_ID, "source": "Salary", "amount": 85000.0,
                                  "incomeDate": "2026-04-30"}
    assert api.received[1][1]["amount"] == 12000.5


def test_excel_errors(tmp_path):
    book = make_workbook(tmp_path / "book.xlsx", {"A": pd.DataFrame({"source": ["x"]})})
    with pytest.raises(ImporterError, match="not found"):
        ei.read_excel_file(tmp_path / "nope.xlsx")
    with pytest.raises(ImporterError, match="Unsupported"):
        ei.read_excel_file(SAMPLES / "income.csv")
    with pytest.raises(ImporterError, match="sheet"):
        ei.read_excel_file(book, "Missing")
    broken = tmp_path / "broken.xlsx"
    broken.write_text("this is not a workbook")
    with pytest.raises(ImporterError, match="Could not"):
        ei.read_excel_file(broken)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def test_cli_exit_codes_and_output(api, tmp_path, capsys):
    ledger = str(tmp_path / "ledger.json")
    base = [str(SAMPLES / "income.csv"), "--user-id", "1", "--api-url", api.url, "--ledger", ledger]
    assert ci.main(base + ["--dry-run"]) == 0
    assert ci.main(base) == 0
    assert "SUCCESS" in capsys.readouterr().out
    assert ci.main(base) == 0                      # already imported -> nothing to do, still fine
    assert ci.main([str(tmp_path / "missing.csv"), "--user-id", "1"]) == 2
    bad = write_csv(tmp_path, "source,amount,date\nSalary,abc,2026-01-01\n")
    assert ci.main([str(bad), "--user-id", "1", "--dry-run", "--ledger", ledger]) == 1
    with pytest.raises(SystemExit):
        ci.main([str(bad)])                        # --user-id is required
