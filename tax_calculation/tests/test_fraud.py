
"""Tests for the fraud engine (fraud_engine/fraud_detector.py + rules.py).

Rows use the column names of database_manager/schema/data.sql.
Run: pytest tests/test_fraud.py -v
"""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fraud_engine"))
from fraud_detector import detect_fraud, get_fraud_alerts, scan_transactions  # noqa: E402


def expense(expense_id, user_id, party_name, amount, expense_date):
    return {"expense_id": expense_id, "user_id": user_id, "category": "General",
            "party_name": party_name, "amount": amount, "expense_date": expense_date}


def income(income_id, user_id, party_name, amount, income_date):
    return {"income_id": income_id, "user_id": user_id, "source": "Salary",
            "party_name": party_name, "amount": amount, "income_date": income_date}


def bank(transaction_id, user_id, transaction_type, party_name, amount, transaction_date):
    return {"transaction_id": transaction_id, "user_id": user_id, "party_name": party_name,
            "transaction_type": transaction_type, "amount": amount,
            "transaction_date": transaction_date}


# Test dataset 1: duplicate expenses
# Expected alerts: 2 (dup of 1), 8 (dup of 7), 9 (dup of 8)
EXPENSES = [
    expense(1, 1, "ABC Traders", 5000, "2026-04-01"),
    expense(2, 1, "  abc  traders", 5000, "2026-04-05"),    # 4 days after 1
    expense(3, 1, "ABC Traders", 5000, "2026-04-20"),       # 15 days later -> OK
    expense(4, 1, "XYZ Supplies", 5000, "2026-04-02"),      # other party -> OK
    expense(5, 1, "ABC Traders", 5200, "2026-04-03"),       # other amount -> OK
    expense(6, 2, "ABC Traders", 5000, "2026-04-02"),       # other user -> OK
    expense(7, 2, "Office Rent", 20000, "2026-05-01"),
    expense(8, 2, "Office Rent", 20000, "2026-05-08"),      # exactly 7 days -> dup
    expense(9, 2, "Office Rent", 20000, "2026-05-09"),      # 1 day after 8 -> dup
    expense(10, 3, "Cloud Hosting", 999, "2026-06-01"),
    expense(11, 3, "Cloud Hosting", 999, "2026-06-09"),     # 8 days -> OK
]

# Test dataset 2: income mismatch
# Expected alerts: income 3 (Client A), income 4 (Beta Ltd), income 6 (Delta), bank 104 (Upwork)
INCOME = [
    income(1, 1, "Acme Corp", 100000, "2026-04-30"),
    income(2, 1, "Acme Corp", 100000, "2026-05-31"),
    income(3, 1, "Client A", 50000, "2026-05-10"),
    income(4, 2, "Beta Ltd", 40000, "2026-06-01"),
    income(5, 2, "Gamma", 60000, "2026-06-05"),
    income(6, 2, "Delta", 25000, "2026-06-07"),
]
BANK = [
    bank(101, 1, "INCOME", "ACME CORP", 100000, "2026-04-30"),
    bank(102, 1, "INCOME", "Acme Corp", 100000, "2026-05-31"),
    bank(103, 1, "INCOME", "Client A", 30000, "2026-05-12"),
    bank(104, 1, "INCOME", "Upwork", 75000, "2026-05-20"),
    bank(105, 2, "INCOME", "Gamma", 60000.50, "2026-06-05"),     # 0.50 off -> within tolerance
    bank(106, 2, "INCOME", "Delta", 40000, "2026-06-08"),
    bank(107, 2, "EXPENSE", "Landlord", 15000, "2026-06-01"),    # money out -> ignored
]


def alerts_by_id(result):
    return {(a["transaction_source"], a["transaction_id"]): a for a in result["alerts"]}


# ---------------- detect_fraud() ----------------

def test_detect_fraud_duplicate_is_true():
    assert detect_fraud(EXPENSES[1], EXPENSES) is True


def test_detect_fraud_first_occurrence_is_false():
    assert detect_fraud(EXPENSES[0], EXPENSES) is False


def test_detect_fraud_matching_income_is_false():
    assert detect_fraud(INCOME[0], BANK) is False


def test_detect_fraud_invalid_row_raises():
    with pytest.raises(ValueError):
        detect_fraud(expense(1, 1, "ABC", -5, "2026-04-01"))


# ---------------- Rule 1: duplicate expenses ----------------

def test_duplicate_alerts_found():
    alerts = alerts_by_id(scan_transactions(expenses=EXPENSES))
    assert set(alerts) == {("EXPENSE", 2), ("EXPENSE", 8), ("EXPENSE", 9)}


def test_duplicate_points_to_original():
    alerts = alerts_by_id(scan_transactions(expenses=EXPENSES))
    assert alerts[("EXPENSE", 2)]["matched_transaction_id"] == 1
    assert alerts[("EXPENSE", 9)]["matched_transaction_id"] == 8
    assert alerts[("EXPENSE", 9)]["matched_source"] == "EXPENSE"


def test_duplicate_difference_is_amount():
    alerts = alerts_by_id(scan_transactions(expenses=EXPENSES))
    assert alerts[("EXPENSE", 8)]["difference_amount"] == 20000


# ---------------- Rule 2: income mismatch ----------------

def scan_income():
    return alerts_by_id(scan_transactions(income=INCOME, bank_transactions=BANK))


def test_income_mismatch_alerts_found():
    assert set(scan_income()) == {("INCOME", 3), ("INCOME", 4), ("INCOME", 6), ("BANK", 104)}


def test_recorded_more_than_received():
    a = scan_income()[("INCOME", 3)]
    assert a["matched_source"] == "BANK"
    assert a["matched_transaction_id"] == 103
    assert a["difference_amount"] == 20000


def test_no_bank_credit():
    a = scan_income()[("INCOME", 4)]
    assert a["matched_transaction_id"] is None
    assert a["difference_amount"] == 40000


def test_under_reported_income():
    a = scan_income()[("INCOME", 6)]
    assert a["difference_amount"] == 15000
    assert "under-reported" in a["reason"]


def test_unreported_bank_income():
    a = scan_income()[("BANK", 104)]
    assert a["difference_amount"] == 75000
    assert "unreported" in a["reason"]


def test_income_without_party_name_uses_source():
    row = {"income_id": 1, "user_id": 1, "source": "Acme Corp", "amount": 100000, "income_date": "2026-04-30"}
    assert detect_fraud(row, BANK) is False


# ---------------- Alert format = fraud_alerts table ----------------

def test_alert_columns_match_fraud_alerts_table():
    result = scan_transactions(EXPENSES, INCOME, BANK)
    for a in result["alerts"]:
        assert set(a) == {"user_id", "fraud_type", "transaction_source", "transaction_id",
                          "matched_source", "matched_transaction_id",
                          "difference_amount", "reason", "status"}
        assert a["fraud_type"] in ("DUPLICATE_EXPENSE", "INCOME_MISMATCH")
        assert a["status"] == "NEEDS_VERIFICATION"
        assert len(a["reason"]) <= 255


# ---------------- Validation ----------------

def test_bad_rows_reported_good_rows_used():
    result = scan_transactions(
        expenses=[
            expense(1, 1, "ABC", 5000, "2026-04-01"),
            expense(1, 1, "ABC", 5000, "2026-04-02"),           # duplicate id
            expense(2, 1, "ABC", -50, "2026-04-02"),            # negative amount
            expense(3, 1, "ABC", 5000, "2026-02-30"),           # bad date
            expense(4, None, "ABC", 5000, "2026-04-02"),        # no user
        ],
        bank_transactions=[bank(1, 1, "TRANSFER", "X", 1, "2026-04-01")],   # bad type
    )
    assert result["ok"] is False
    assert len(result["errors"]) == 5
    assert result["summary"]["checked"] == 1


def test_database_types_accepted():
    rows = [
        expense(1, 7, "ABC", Decimal("999.50"), date(2026, 4, 1)),
        expense(2, 7, "abc", Decimal("999.50"), date(2026, 4, 3)),
    ]
    alerts = get_fraud_alerts(rows[1], rows)
    assert len(alerts) == 1
    assert alerts[0]["difference_amount"] == 999.5


def test_empty_scan():
    result = scan_transactions()
    assert result["ok"] is True
    assert result["alerts"] == []
