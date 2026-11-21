"""Fraud and anomaly detection rules.

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
from __future__ import annotations
import re

STATUS = "NEEDS_VERIFICATION"

DUPLICATE_WINDOW_DAYS = 7    # Rule 1: same expense again within 7 days
MATCH_WINDOW_DAYS = 7        # Rule 2: bank credit expected within 7 days of income
MISMATCH_TOLERANCE = 1.0     # Rule 2: ignore differences up to Rs 1.00


def normalize_party(name: str) -> str:
    """
    Cleans vendor and counterparty names:
    - Removes UPI/NEFT/IMPS/RTGS/POS prefixes.
    - Strips UPI VPA handles (e.g., '@okhdfcbank', '@paytm', '@ybl').
    - Removes trailing reference and transaction numbers.
    """
    if not name:
        return ""
    cleaned = " ".join(name.split()).upper()

    for prefix in ("UPI/", "NEFT/", "IMPS/", "RTGS/", "POS/", "ACH/", "INB/"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    cleaned = re.sub(r"@[A-Z0-9]+", "", cleaned)

    parts = re.split(r"[/|-]", cleaned)
    if parts and parts[0].strip():
        cleaned = parts[0].strip()

    return cleaned


def _is_self_transfer_or_refund(t: dict) -> bool:
    party = normalize_party(t.get("party_name") or "")
    return any(keyword in party for keyword in ("SELF", "OWN ACC", "INTERNAL TRANSFER", "REFUND", "REVERSAL"))


def _same_user_and_party(a: dict, b: dict) -> bool:
    return a["user_id"] == b["user_id"] and normalize_party(a["party_name"]) == normalize_party(b["party_name"])


def _days_apart(a: dict, b: dict) -> int:
    return abs((a["date"] - b["date"]).days)


def _is_bank_income(t: dict) -> bool:
    return t["source"] == "BANK" and t["transaction_type"] == "INCOME" and not _is_self_transfer_or_refund(t)


def _alert(fraud_type: str, t: dict, matched: dict | None, difference: float, reason: str) -> dict:
    """Generates one standardized row for the fraud_alerts table."""
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


def check_duplicate_expense(transaction: dict, history: list[dict]):
    """
    An EXPENSE is a possible duplicate if an EARLIER expense has the same
    user, same party_name and same amount, within DUPLICATE_WINDOW_DAYS.
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
        and abs(round(h["amount"], 2) - round(t["amount"], 2)) <= 0.05
        and _days_apart(h, t) <= DUPLICATE_WINDOW_DAYS
    ]
    if not earlier:
        return None

    original = max(earlier, key=lambda h: (h["date"], str(h["id"])))
    days = _days_apart(original, t)
    timing_str = "on the same day" if days == 0 else f"{days} day(s) earlier"

    return _alert(
        "DUPLICATE_EXPENSE",
        t,
        original,
        t["amount"],
        f"Expense of Rs {t['amount']:.2f} to '{t['party_name']}' was already recorded "
        f"{timing_str} (expense ID {original['id']}). Possible duplicate entry.",
    )


def check_income_mismatch(transaction: dict, history: list[dict]):
    """
    INCOME row: find the bank transaction of type INCOME from the same user
                and party within MATCH_WINDOW_DAYS.
    BANK INCOME row: alert if no corresponding income was recorded.
    """
    t = transaction

    if t["source"] == "INCOME":
        credits = [
            h for h in history
            if _is_bank_income(h) and _same_user_and_party(h, t)
            and _days_apart(h, t) <= MATCH_WINDOW_DAYS
        ]
        if not credits:
            return _alert(
                "INCOME_MISMATCH",
                t,
                None,
                t["amount"],
                f"Income of Rs {t['amount']:.2f} recorded from '{t['party_name']}' "
                f"but no matching bank credit found within {MATCH_WINDOW_DAYS} days.",
            )

        bank = min(credits, key=lambda h: (abs(h["amount"] - t["amount"]), _days_apart(h, t)))
        diff = abs(t["amount"] - bank["amount"])
        if diff <= MISMATCH_TOLERANCE:
            return None

        expected_net_10_percent = t["amount"] * 0.90
        if abs(bank["amount"] - expected_net_10_percent) <= MISMATCH_TOLERANCE:
            reason = (
                f"Bank credited Rs {bank['amount']:.2f} vs invoice Rs {t['amount']:.2f} "
                f"(Section 194J/194C TDS deduction noted. Reconcile Form 26AS/AIS)."
            )
        elif bank["amount"] > t["amount"]:
            reason = (
                f"Bank received Rs {bank['amount']:.2f} from '{t['party_name']}' but only "
                f"Rs {t['amount']:.2f} recorded as income. Possible under-reported income."
            )
        else:
            reason = (
                f"Recorded income Rs {t['amount']:.2f} from '{t['party_name']}' but bank "
                f"shows only Rs {bank['amount']:.2f} received."
            )

        return _alert("INCOME_MISMATCH", t, bank, diff, reason)

    if _is_bank_income(t):
        recorded = any(
            h["source"] == "INCOME" and _same_user_and_party(h, t)
            and _days_apart(h, t) <= MATCH_WINDOW_DAYS
            for h in history
        )
        if recorded:
            return None

        return _alert(
            "INCOME_MISMATCH",
            t,
            None,
            t["amount"],
            f"Bank received Rs {t['amount']:.2f} from '{t['party_name']}' "
            f"but no income was recorded in books. Possible unreported income.",
        )

    return None


FRAUD_RULES = (check_duplicate_expense, check_income_mismatch)
