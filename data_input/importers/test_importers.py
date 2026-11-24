"""
Tests for csv_importer.py and excel_importer.py.

Run from the project root:
    python -m pytest data_input/importers/test_importers.py -v

The first half needs only pandas. The second half ("real backend") starts the
actual TaxSaint FastAPI app on a temporary SQLite database and imports into it,
so it checks the importer against the real endpoints, schemas and fraud scan.
"""

import io
import os
import socket
import subprocess
import sys
import time
import uuid
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data_input.importers import csv_importer as ci      # noqa: E402
from data_input.importers import excel_importer as ei    # noqa: E402
from data_input.importers.csv_importer import ImporterError  # noqa: E402

SAMPLES = PROJECT_ROOT / "data_input" / "sample_data"
DEAD_URL = "http://127.0.0.1:9"      # nothing listens here


def write_csv(tmp_path, text):
    path = tmp_path / "data.csv"
    path.write_text(text, encoding="utf-8")
    return path


def row(**values):
    return pd.Series(values, dtype=object)


# ---------------------------------------------------------------------------
# Reading and cleaning
# ---------------------------------------------------------------------------

def test_read_csv_errors(tmp_path):
    with pytest.raises(ImporterError, match="not found"):
        ci.read_csv_file(tmp_path / "missing.csv")
    with pytest.raises(ImporterError, match="Could not read"):
        ci.read_csv_file(write_csv(tmp_path, ""))


def test_clean_dataframe_tidies_headers_and_keeps_row_numbers(tmp_path):
    df = ci.read_csv_file(write_csv(tmp_path, "Party Name,Income Date\n A ,1\n,\nB,2\n"))
    cleaned = ci.clean_dataframe(df)
    assert list(cleaned.columns) == ["party_name", "date"]    # "Income Date" -> date
    assert list(cleaned.index) == [0, 2]                      # blank row dropped, numbering kept
    assert cleaned.loc[0, "party_name"] == "A"                # spaces stripped


def test_clean_dataframe_rejects_duplicate_columns():
    df = pd.DataFrame([["1", "2"]], columns=["date", "Income Date"])
    with pytest.raises(ImporterError, match="duplicate column"):
        ci.clean_dataframe(df)


# ---------------------------------------------------------------------------
# Type detection and columns
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("columns, expected", [
    (["source", "amount", "date"], "income"),
    (["category", "party_name", "amount", "date"], "expense"),
    (["party_name", "transaction_type", "amount", "date"], "bank_transaction"),
])
def test_detect_transaction_type(columns, expected):
    assert ci.detect_transaction_type(pd.DataFrame(columns=columns)) == expected


@pytest.mark.parametrize("columns", [["amount", "date"], ["source", "category"]])
def test_detect_transaction_type_unclear(columns):
    with pytest.raises(ImporterError, match="Could not tell"):
        ci.detect_transaction_type(pd.DataFrame(columns=columns))


def test_validate_columns_lists_missing():
    assert ci.validate_columns(pd.DataFrame(columns=["source", "amount"]), "income") == ["date"]
    assert ci.validate_columns(pd.DataFrame(columns=["category", "amount"]), "expense") == ["party_name", "date"]


# ---------------------------------------------------------------------------
# Amount, date and row validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [("1500", "1500.00"), ("1,234.5", "1234.50"), ("0.01", "0.01")])
def test_parse_amount_valid(text, expected):
    assert str(ci.parse_amount(text)) == expected


@pytest.mark.parametrize("text", ["abc", "0", "-5", "12.345", "NaN", "inf", "10000000000"])
def test_parse_amount_invalid(text):
    with pytest.raises(ValueError):
        ci.parse_amount(text)


@pytest.mark.parametrize("text", ["2026-04-30", "30/04/2026", "2026-04-30 00:00:00"])
def test_parse_date_valid(text):
    assert ci.parse_date(text) == date(2026, 4, 30)


def test_parse_date_invalid_and_future_allowed():
    for text in ["30-04-2026", "04/30/2026", "tomorrow", "2026-02-31"]:
        with pytest.raises(ValueError, match="date must look like"):
            ci.parse_date(text)
    # Future dates are accepted: demo salary data covers the whole financial year.
    assert ci.parse_date("2027-03-31") == date(2027, 3, 31)


GOOD_INCOME = dict(source="Salary", amount="10", date="2026-01-01")
GOOD_EXPENSE = dict(category="Rent", party_name="Sharma", amount="10", date="2026-01-01")
GOOD_BANK = dict(transaction_type="INCOME", amount="10", date="2026-01-01")


@pytest.mark.parametrize("record_type, good, change, column", [
    ("income", GOOD_INCOME, {"source": None}, "source"),
    ("income", GOOD_INCOME, {"amount": "-1"}, "amount"),
    ("income", GOOD_INCOME, {"date": "31/31/2026"}, "date"),
    ("income", GOOD_INCOME, {"source": "x" * 51}, "source"),
    ("income", GOOD_INCOME, {"party_name": "x" * 101}, "party_name"),
    ("expense", GOOD_EXPENSE, {"party_name": None}, "party_name"),
    ("expense", GOOD_EXPENSE, {"amount": "1.234"}, "amount"),
    ("bank_transaction", GOOD_BANK, {"transaction_type": "REFUND"}, "transaction_type"),
])
def test_validate_row_finds_problem(record_type, good, change, column):
    errors = ci.validate_row(row(**{**good, **change}), 5, record_type)
    assert [(e.row, e.column) for e in errors] == [(5, column)]


def test_validate_row_accepts_good_rows_and_optional_party_name():
    assert ci.validate_row(row(**GOOD_INCOME), 2, "income") == []          # party_name is optional
    assert ci.validate_row(row(**GOOD_BANK, party_name="Acme"), 2, "bank_transaction") == []
    assert ci.validate_row(row(**{**GOOD_BANK, "transaction_type": "income"}), 2, "bank_transaction") == []


def test_split_valid_invalid_reports_file_row_numbers(tmp_path):
    df = ci.clean_dataframe(ci.read_csv_file(write_csv(
        tmp_path, "source,amount,date\nSalary,1000,2026-01-01\nBonus,abc,2026-01-02\n,5,2026-01-03\n")))
    valid, invalid, errors = ci.split_valid_invalid(df, "income")
    assert (len(valid), len(invalid)) == (1, 2)
    assert [(e.row, e.column) for e in errors] == [(3, "amount"), (4, "source")]


# ---------------------------------------------------------------------------
# Conversion to the API format
# ---------------------------------------------------------------------------

def test_convert_uses_backend_field_names():
    income = ci.clean_dataframe(pd.DataFrame([{**GOOD_INCOME, "amount": "1,000.5", "date": "30/04/2026"}]))
    assert ci.convert_to_internal_format(income, "income", 7) == [
        {"user_id": 7, "source": "Salary", "amount": "1000.50", "income_date": "2026-04-30"}]

    income = ci.clean_dataframe(pd.DataFrame([{**GOOD_INCOME, "party_name": "Acme"}]))
    assert ci.convert_to_internal_format(income, "income", 7)[0]["party_name"] == "Acme"

    expense = ci.clean_dataframe(pd.DataFrame([GOOD_EXPENSE]))
    assert ci.convert_to_internal_format(expense, "expense", 7)[0] == {
        "user_id": 7, "category": "Rent", "party_name": "Sharma", "amount": "10.00", "expense_date": "2026-01-01"}

    bank = ci.clean_dataframe(pd.DataFrame([{**GOOD_BANK, "transaction_type": "income"}]))
    assert ci.convert_to_internal_format(bank, "bank_transaction", 7)[0] == {
        "user_id": 7, "transaction_type": "INCOME", "amount": "10.00", "transaction_date": "2026-01-01"}


# ---------------------------------------------------------------------------
# Whole imports that need no backend
# ---------------------------------------------------------------------------

def test_dry_run_contacts_no_api():
    summary = ci.import_csv(SAMPLES / "expense.csv", 1, dry_run=True, api_base_url=DEAD_URL)
    assert (summary.status, summary.valid_count, summary.sent_count) == (ci.DRY_RUN, 3, 0)


def test_missing_column_is_rejected(tmp_path):
    summary = ci.import_csv(write_csv(tmp_path, "category,amount\nRent,10\n"), 1, api_base_url=DEAD_URL)
    assert summary.status == ci.REJECTED
    assert {e.column for e in summary.errors} == {"party_name", "date"}


def test_header_only_file_and_bad_user_id(tmp_path):
    with pytest.raises(ImporterError, match="no data rows"):
        ci.import_csv(write_csv(tmp_path, "source,amount,date\n"), 1, dry_run=True)
    for bad in (0, -1, "1", None):
        with pytest.raises(ImporterError, match="user_id"):
            ci.import_csv(SAMPLES / "income.csv", bad, dry_run=True)


def test_unreachable_api_stops_after_first_failure():
    summary = ci.import_csv(SAMPLES / "income.csv", 1, api_base_url=DEAD_URL)
    assert summary.status == ci.FAILED and summary.sent_count == 0
    assert len(summary.send_errors) == 1 and "Could not reach" in summary.message


def test_process_file_stream_rejects_unknown_type():
    with pytest.raises(ImporterError, match="Unsupported file type"):
        ci.process_file_stream(b"data", "notes.txt", 1)


def test_excel_reading_and_errors(tmp_path):
    book = tmp_path / "book.xlsx"
    with pd.ExcelWriter(book) as writer:
        pd.DataFrame({"x": [1]}).to_excel(writer, sheet_name="Notes", index=False)
        pd.DataFrame({"Source": ["Salary"], "Amount": [85000],
                      "Date": [pd.Timestamp("2026-04-30")]}).to_excel(writer, sheet_name="Income", index=False)
    summary = ei.import_excel(book, 1, "Income", dry_run=True)
    assert (summary.transaction_type, summary.valid_count) == ("income", 1)
    in_memory = ei.read_excel_file(io.BytesIO(book.read_bytes()), "Income")     # as the upload route does
    assert in_memory.iloc[0]["Source"] == "Salary"
    with pytest.raises(ImporterError, match="not found"):
        ei.read_excel_file(tmp_path / "missing.xlsx")
    with pytest.raises(ImporterError, match="Could not read"):
        ei.read_excel_file(book, "NoSuchSheet")
    broken = tmp_path / "broken.xlsx"
    broken.write_text("not a workbook")
    with pytest.raises(ImporterError, match="Could not read"):
        ei.read_excel_file(broken)


def test_command_line_exit_codes(tmp_path, capsys):
    good = [str(SAMPLES / "income.csv"), "--user-id", "1", "--dry-run"]
    assert ci.main(good) == 0 and "DRY_RUN" in capsys.readouterr().out
    bad = write_csv(tmp_path, "source,amount,date\nSalary,abc,2026-01-01\n")
    assert ci.main([str(bad), "--user-id", "1", "--dry-run"]) == 1
    assert ci.main([str(tmp_path / "missing.csv"), "--user-id", "1"]) == 2
    with pytest.raises(SystemExit):
        ci.main([str(bad)])                                 # --user-id is required


# ---------------------------------------------------------------------------
# Real backend: the actual FastAPI app on a temporary SQLite database
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def backend(tmp_path_factory):
    pytest.importorskip("uvicorn")
    pytest.importorskip("fastapi")
    pytest.importorskip("multipart")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    # The upload route makes the importer call this same server, so it must know its own address.
    env = {**os.environ, "AUTH_SECRET_KEY": "test-secret", "TAXSAINT_API_BASE_URL": url,
           "DATABASE_URL": f"sqlite:///{tmp_path_factory.mktemp('db') / 'test.db'}"}
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "integration.api.main:app", "--port", str(port)],
        cwd=PROJECT_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                if requests.get(url + "/health", timeout=1).ok:
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            pytest.fail("The backend did not start")
        yield url
    finally:
        server.terminate()
        server.wait(timeout=10)


@pytest.fixture
def user_id(backend):
    """A fresh user for each test, so tests never see each other's records."""
    response = requests.post(backend + "/api/users", json={
        "name": "Importer Test", "email": f"{uuid.uuid4().hex}@example.com", "userType": "salaried"})
    assert response.status_code == 201, response.text
    return response.json()["user_id"]


@pytest.mark.parametrize("name, record_type", [
    ("income.csv", "income"), ("expense.csv", "expense"), ("bank_transactions.csv", "bank_transaction"),
])
def test_sample_files_import_into_real_backend(backend, user_id, name, record_type):
    summary = ci.import_csv(SAMPLES / name, user_id, api_base_url=backend)
    assert (summary.transaction_type, summary.status, summary.sent_count) == (record_type, ci.SUCCESS, 3)


def test_imported_rows_are_saved_with_the_right_values(backend, user_id):
    ci.import_csv(SAMPLES / "income.csv", user_id, api_base_url=backend)
    saved = requests.get(f"{backend}/api/financial/income/{user_id}").json()
    file_rows = pd.read_csv(SAMPLES / "income.csv", dtype=str)
    expected = sorted((r.source, float(r.amount), r.date) for r in file_rows.itertuples())
    assert sorted((r["source"], r["amount"], r["income_date"]) for r in saved) == expected


def test_projected_future_dates_are_imported(backend, user_id):
    summary = ci.import_csv(SAMPLES / "demo_salary_statement.csv", user_id, api_base_url=backend)
    assert summary.status == ci.SUCCESS and summary.invalid_count == 0


def test_invalid_rows_are_reported_and_valid_rows_still_sent(backend, user_id, tmp_path):
    path = write_csv(tmp_path, "source,amount,date\nSalary,1000,2026-01-01\nBonus,oops,2026-01-02\n")
    summary = ci.import_csv(path, user_id, api_base_url=backend)
    assert (summary.status, summary.sent_count, summary.invalid_count) == (ci.PARTIAL, 1, 1)
    assert [(e.row, e.column) for e in summary.errors] == [(3, "amount")]


def test_backend_rejection_is_reported(backend):
    summary = ci.import_csv(SAMPLES / "income.csv", 999999, api_base_url=backend)   # no such user
    assert summary.status == ci.FAILED and summary.sent_count == 0
    assert "User not found" in summary.send_errors[0]


def test_skip_existing_avoids_duplicates_only_when_asked(backend, user_id):
    ci.import_csv(SAMPLES / "income.csv", user_id, api_base_url=backend)
    again = ci.import_csv(SAMPLES / "income.csv", user_id, skip_existing=True, api_base_url=backend)
    assert (again.status, again.duplicate_count, again.sent_count) == (ci.NO_NEW_RECORDS, 3, 0)
    assert len(requests.get(f"{backend}/api/financial/income/{user_id}").json()) == 3
    ci.import_csv(SAMPLES / "income.csv", user_id, api_base_url=backend)             # default: send everything
    assert len(requests.get(f"{backend}/api/financial/income/{user_id}").json()) == 6


def test_duplicate_expenses_reach_the_fraud_engine(backend, user_id, tmp_path):
    path = write_csv(tmp_path, "category,party_name,amount,date\n"
                               "Travel,IndiGo,500,2026-06-01\nTravel,IndiGo,500,2026-06-01\n")
    assert ci.import_csv(path, user_id, api_base_url=backend).sent_count == 2
    alerts = requests.get(f"{backend}/api/fraud/alerts/{user_id}").json()["alerts"]
    assert any("DUPLICATE" in alert["type"] for alert in alerts)


def test_upload_route_uses_the_importer(backend, user_id):
    """POST /api/financial/upload calls process_file_stream (CSV and Excel)."""
    with open(SAMPLES / "income.csv", "rb") as f:
        result = requests.post(backend + "/api/financial/upload", data={"user_id": user_id},
                               files={"file": ("income.csv", f)}, timeout=60).json()
    assert (result["ok"], result["status"], result["imported"], result["transaction_type"]) == (True, "success", 3, "income")

    book = io.BytesIO()
    pd.DataFrame({"category": ["Rent"], "party_name": ["Sharma"], "amount": [18000],
                  "date": [pd.Timestamp("2026-05-01")]}).to_excel(book, index=False)
    result = requests.post(backend + "/api/financial/upload", data={"user_id": user_id},
                           files={"file": ("expenses.xlsx", book.getvalue())}, timeout=60).json()
    assert (result["ok"], result["imported"], result["transaction_type"]) == (True, 1, "expense")

    bad = requests.post(backend + "/api/financial/upload", data={"user_id": user_id},
                        files={"file": ("notes.txt", b"hello")}, timeout=60)
    assert bad.status_code == 422 and "Unsupported file type" in bad.json()["detail"]
