"""Fraud detection rules.

Each rule checks ONE transaction against the user's other records
(`history`) and returns an alert dict, or None if it looks fine.
Rules never touch the database and never confirm fraud.

Transactions arrive already cleaned by fraud_detector.py:
    {"source": "EXPENSE" | "INCOME" | "BANK",
     "id": expense_id / income_id / transaction_id,
     "user_id", "party_name", "amount": float, "date": datetime.date,
     "transaction_type": "INCOME" | "EXPENSE"   (BANK only)}

Alerts use the columns of the fraud_alerts table.
"""

STATUS = "NEEDS_VERIFICATION"

DUPLICATE_WINDOW_DAYS = 7    # Rule 1: same expense again within 7 days
MATCH_WINDOW_DAYS = 7        # Rule 2: bank credit expected within 7 days of income
MISMATCH_TOLERANCE = 1.0     # Rule 2: ignore differences up to Rs 1


def normalize_party(name: str) -> str:
    """'  abc  Traders ' -> 'ABC TRADERS' so names match reliably."""
    return " ".join(name.split()).upper()


def _same_user_and_party(a: dict, b: dict) -> bool:
    return a["user_id"] == b["user_id"] and normalize_party(a["party_name"]) == normalize_party(b["party_name"])


def _days_apart(a: dict, b: dict) -> int:
    return abs((a["date"] - b["date"]).days)


def _is_bank_income(t: dict) -> bool:
    return t["source"] == "BANK" and t["transaction_type"] == "INCOME"


def _alert(fraud_type: str, t: dict, matched, difference: float, reason: str) -> dict:
    """One row for the fraud_alerts table."""
    return {
        "user_id": t["user_id"],
        "fraud_type": fraud_type,
        "transaction_source": t["source"],
        "transaction_id": t["id"],
        "matched_source": matched["source"] if matched else None,
        "matched_transaction_id": matched["id"] if matched else None,
        "difference_amount": round(difference, 2),
        "reason": reason,
        "status": STATUS,
    }


# ------------------------------------------------------------------
# Rule 1: Duplicate expense
# ------------------------------------------------------------------
def check_duplicate_expense(transaction: dict, history: list[dict]):
    """
    An EXPENSE is a possible duplicate if an EARLIER expense has the same
    user, same party_name and same amount, within DUPLICATE_WINDOW_DAYS.
    Only earlier ones are checked, so each duplicate pair is reported once.
    """
    t = transaction
    if t["source"] != "EXPENSE":
        return None

    earlier = [
        h for h in history
        if h["source"] == "EXPENSE"
        and h["id"] != t["id"]
        and (h["date"], str(h["id"])) < (t["date"], str(t["id"]))
        and _same_user_and_party(h, t)
        and round(h["amount"], 2) == round(t["amount"], 2)
        and _days_apart(h, t) <= DUPLICATE_WINDOW_DAYS
    ]
    if not earlier:
        return None

    original = max(earlier, key=lambda h: (h["date"], str(h["id"])))   # closest earlier one
    return _alert(
        "DUPLICATE_EXPENSE", t, original, t["amount"],
        f"Expense of Rs {t['amount']:.2f} to '{t['party_name']}' was already recorded "
        f"{_days_apart(original, t)} day(s) earlier (expense {original['id']}). Possible duplicate entry.",
    )


# ------------------------------------------------------------------
# Rule 2: Income mismatch
# ------------------------------------------------------------------
def check_income_mismatch(transaction: dict, history: list[dict]):
    """
    INCOME row: find the bank transaction of type INCOME from the same user
                and party within MATCH_WINDOW_DAYS. Alert if none exists or
                the amounts differ by more than MISMATCH_TOLERANCE.
    BANK INCOME row: alert if no income was recorded for it (unreported income).
    EXPENSE rows and BANK EXPENSE rows: ignored.
    """
    t = transaction

    if t["source"] == "INCOME":
        credits = [h for h in history
                   if _is_bank_income(h) and _same_user_and_party(h, t)
                   and _days_apart(h, t) <= MATCH_WINDOW_DAYS]
        if not credits:
            return _alert(
                "INCOME_MISMATCH", t, None, t["amount"],
                f"Income of Rs {t['amount']:.2f} recorded from '{t['party_name']}' "
                f"but no matching bank credit found within {MATCH_WINDOW_DAYS} days.",
            )

        bank = min(credits, key=lambda h: (abs(h["amount"] - t["amount"]), _days_apart(h, t)))
        diff = abs(t["amount"] - bank["amount"])
        if diff <= MISMATCH_TOLERANCE:
            return None

        if bank["amount"] > t["amount"]:
            reason = (f"Bank received Rs {bank['amount']:.2f} from '{t['party_name']}' but only "
                      f"Rs {t['amount']:.2f} recorded as income. Possible under-reported income.")
        else:
            reason = (f"Recorded income Rs {t['amount']:.2f} from '{t['party_name']}' but bank "
                      f"shows only Rs {bank['amount']:.2f} received.")
        return _alert("INCOME_MISMATCH", t, bank, diff, reason)

    if _is_bank_income(t):
        recorded = any(h["source"] == "INCOME" and _same_user_and_party(h, t)
                       and _days_apart(h, t) <= MATCH_WINDOW_DAYS for h in history)
        if recorded:
            return None          # the INCOME side checks the amounts
        return _alert(
            "INCOME_MISMATCH", t, None, t["amount"],
            f"Bank received Rs {t['amount']:.2f} from '{t['party_name']}' "
            f"but no income was recorded. Possible unreported income.",
        )

    return None


# ------------------------------------------------------------------
# All rules, in the order they run.
# Each rule: rule(transaction, history) -> alert dict, or None if OK
# ------------------------------------------------------------------
FRAUD_RULES = (check_duplicate_expense, check_income_mismatch)
