# Fraud Engine

Python module that flags **possible** fraud in a user's financial records. It never accesses the database. The backend loads rows from Supabase, using the column names in `database_manager/schema/data.sql`, and passes them in as dicts.

| File | Purpose |
|---|---|
| `rules.py` | `FRAUD_RULES`. Each rule checks **one row** against the user's other rows. |
| `fraud_detector.py` | Entry points: `detect_fraud()`, `get_fraud_alerts()` and `scan_transactions()` |

Every alert has `status = 'NEEDS_VERIFICATION'`. The engine **never** confirms fraud. Only a user or admin can change the status later, to `VERIFIED` or `DISMISSED`.

## Input rows (same columns as the database)

| Table | Columns used |
|---|---|
| `expenses` | `expense_id`, `user_id`, `party_name`, `amount`, `expense_date` |
| `income` | `income_id`, `user_id`, `party_name`, `amount`, `income_date` |
| `bank_transactions` | `transaction_id`, `user_id`, `party_name`, `transaction_type` (`INCOME` / `EXPENSE`), `amount`, `transaction_date` |

- **Table detection.** The engine works out which table a row came from by its ID column.
- **Value types.** `Decimal`, `date` and `int` values straight from SQLAlchemy are accepted.
- **Missing `party_name`.** If an income row has no `party_name`, the engine uses `source` instead.

## Entry points

| Function | Use it when | Returns |
|---|---|---|
| `detect_fraud(row, history=())` | A new row is saved and you need a quick yes/no answer | `bool` |
| `get_fraud_alerts(row, history=())` | Same as above, but you want the details | `list[dict]` |
| `scan_transactions(expenses, income, bank_transactions)` | Checking all of a user's rows, such as one financial year | `{"ok", "summary", "alerts", "errors"}` |

`history` is the user's other rows, from any of the three tables. An invalid `row` raises `ValueError`. Invalid rows in `history` are skipped. In `scan_transactions`, invalid rows are listed in `errors` and the rest are still checked.

```python
from tax_calculation.fraud_engine.fraud_detector import scan_transactions

result = scan_transactions(
    expenses=[row._asdict() for row in expense_rows],
    income=[row._asdict() for row in income_rows],
    bank_transactions=[row._asdict() for row in bank_rows],
)
for alert in result["alerts"]:
    db.execute(insert(FraudAlert).values(**alert))   # keys = fraud_alerts columns
```

## Rule 1: `check_duplicate_expense`

An expense is flagged when an **earlier** expense has the **same `user_id`, `party_name` and `amount`** and is dated within 7 days.

- Names are compared ignoring case and extra spaces.
- The 7-day window is inclusive.
- Each duplicate pair produces one alert, raised on the later expense, with `matched_transaction_id` pointing to the earlier one.

## Rule 2: `check_income_mismatch`

| Row | Check | Alert when |
|---|---|---|
| `income` | Look for a `bank_transactions` row of type `INCOME` with the same user and `party_name`, within 7 days | No bank row is found, or the amounts differ by more than ₹1 |
| `bank_transactions` of type `INCOME` | Look for an `income` row from the same party within 7 days | No income was recorded (possible unreported income) |
| `expenses`, and bank rows of type `EXPENSE` | — | Never |

The limits are `DUPLICATE_WINDOW_DAYS`, `MATCH_WINDOW_DAYS` and `MISMATCH_TOLERANCE`, at the top of `rules.py`.

## Alert = one `fraud_alerts` row

```json
{
  "user_id": 1,
  "fraud_type": "INCOME_MISMATCH",
  "transaction_source": "INCOME",
  "transaction_id": 3,
  "matched_source": "BANK",
  "matched_transaction_id": 103,
  "difference_amount": 20000.0,
  "reason": "Recorded income Rs 50000.00 from 'Client A' but bank shows only Rs 30000.00 received.",
  "status": "NEEDS_VERIFICATION"
}
```

| Key | Meaning |
|---|---|
| `transaction_source` / `matched_source` | The table the ID belongs to: `EXPENSE`, `INCOME` or `BANK` |
| `matched_transaction_id` | `null` when there is nothing to match, for example no bank credit found |
| `difference_amount` | Always ≥ 0 |
| `reason` | Under 255 characters, and can be shown directly in the UI |

`alert_id` and `detected_at` are filled in by the database. The table's `UNIQUE (fraud_type, transaction_source, transaction_id)` constraint stops re-runs from inserting the same alert twice, so use `ON CONFLICT DO NOTHING`.

## Notes for the backend

- **Batch scope.** Scan one user's financial year at a time.
- **Party names.** Clean bank descriptions down to the counterparty name, for example `UPI/ACME CORP/1234` → `ACME CORP`.
- **Bank income rows.** Self-transfers and refunds stored as `INCOME` show up as "unreported income", so exclude them where possible.

## Tests

```bash
cd tax_calculation
pytest tests/test_fraud.py -v
```
