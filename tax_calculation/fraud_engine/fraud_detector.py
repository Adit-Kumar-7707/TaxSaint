
"""Fraud detection entry points."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

try:                                    # works as a package or as plain files
    from .rules import FRAUD_RULES
except ImportError:
    from rules import FRAUD_RULES

# Which table a row comes from is detected by its id column,
# using the column names of database_manager/schema/data.sql
TABLES = {
    "EXPENSE": {"id": "expense_id", "date": "expense_date"},
    "INCOME": {"id": "income_id", "date": "income_date"},
    "BANK": {"id": "transaction_id", "date": "transaction_date"},
}


def _source_of(row: dict) -> str:
    for source, columns in TABLES.items():
        if columns["id"] in row:
            return source
    raise ValueError("row needs expense_id, income_id or transaction_id")


def clean_transaction(row: dict) -> dict:
    """Validate one database row and convert its fields. Raises ValueError if invalid."""
    if not isinstance(row, dict):
        raise ValueError("transaction must be a dict")

    source = _source_of(row)
    columns = TABLES[source]

    def text(column):
        value = row.get(column)
        value = "" if value is None else str(value).strip()
        if not value:
            raise ValueError(f"{column} is empty")
        return value

    # income rows may still use "source" until party_name is added to the table
    party_column = "party_name" if row.get("party_name") or source != "INCOME" else "source"

    try:
        amount = float(Decimal(str(row.get("amount"))))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("amount must be a number")
    if amount <= 0:
        raise ValueError("amount must be greater than 0")

    raw_date = row.get(columns["date"])
    if isinstance(raw_date, datetime):
        row_date = raw_date.date()
    elif isinstance(raw_date, date):
        row_date = raw_date
    else:
        try:
            row_date = datetime.strptime(str(raw_date), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"{columns['date']} must be a valid YYYY-MM-DD")

    text(columns["id"])                    # raises if empty
    text("user_id")

    clean = {
        "source": source,
        "id": row[columns["id"]],          # original value (int from the database)
        "user_id": row["user_id"],
        "party_name": text(party_column),
        "amount": amount,
        "date": row_date,
        "transaction_type": None,
    }
    if source == "BANK":
        clean["transaction_type"] = text("transaction_type").upper()
        if clean["transaction_type"] not in ("INCOME", "EXPENSE"):
            raise ValueError("transaction_type must be INCOME or EXPENSE")
    return clean


def _clean_history(history) -> list[dict]:
    """Clean history rows; invalid rows are simply left out."""
    cleaned = []
    for row in history or ():
        try:
            cleaned.append(clean_transaction(row))
        except ValueError:
            pass
    return cleaned


def get_fraud_alerts(transaction: dict, history=()) -> list[dict]:
    """Return every alert raised for one transaction (empty list = looks fine)."""
    t = clean_transaction(transaction)
    h = _clean_history(history)
    return [alert for alert in (rule(t, h) for rule in FRAUD_RULES) if alert]


def detect_fraud(transaction: dict, history=()) -> bool:
    """Return whether a transaction matches a fraud rule."""
    t = clean_transaction(transaction)
    h = _clean_history(history)
    return any(rule(t, h) for rule in FRAUD_RULES)


def scan_transactions(expenses=(), income=(), bank_transactions=()) -> dict:
    """
    Check all of a user's rows in one call (e.g. one financial year).
    Each row is compared with all the others.
    Returns {"ok", "summary", "alerts", "errors"}; bad rows go to "errors".
    Each alert is ready to insert into the fraud_alerts table.
    """
    valid, errors, seen = [], [], set()
    for table, rows in (("expenses", expenses), ("income", income), ("bank_transactions", bank_transactions)):
        for index, row in enumerate(rows or ()):
            try:
                t = clean_transaction(row)
                if (t["source"], t["id"]) in seen:
                    raise ValueError(f"duplicate id in {table}")
                seen.add((t["source"], t["id"]))
                valid.append(t)
            except ValueError as e:
                errors.append({"table": table, "index": index, "message": str(e)})

    alerts = []
    for t in valid:
        others = [o for o in valid if o is not t]
        alerts.extend(a for a in (rule(t, others) for rule in FRAUD_RULES) if a)

    return {
        "ok": not errors,
        "summary": {"checked": len(valid), "alerts": len(alerts)},
        "alerts": alerts,
        "errors": errors,
    }
