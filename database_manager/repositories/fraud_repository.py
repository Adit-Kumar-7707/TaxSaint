"""Fraud repository."""

from sqlalchemy import text
from database_manager.connection import engine


def find_duplicate_expenses(user_id: int):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    user_id,
                    LOWER(TRIM(party_name)) AS party_name,
                    amount,
                    expense_date,
                    COUNT(*) AS occurrence_count,
                    ARRAY_AGG(expense_id ORDER BY expense_id) AS expense_ids
                FROM expenses
                WHERE user_id = :user_id
                GROUP BY
                    user_id,
                    LOWER(TRIM(party_name)),
                    amount,
                    expense_date
                HAVING COUNT(*) > 1
                ORDER BY expense_date DESC
            """),
            {"user_id": user_id},
        )

        return [dict(row) for row in result.mappings().all()]


def save_duplicate_alerts(user_id: int):
    duplicates = find_duplicate_expenses(user_id)
    saved_alerts = []

    with engine.begin() as connection:
        for group in duplicates:
            expense_ids = group["expense_ids"]
            primary_id = expense_ids[0]

            for duplicate_id in expense_ids[1:]:
                result = connection.execute(
                    text("""
                        INSERT INTO fraud_alerts (
                            user_id,
                            fraud_type,
                            transaction_source,
                            transaction_id,
                            matched_source,
                            matched_transaction_id,
                            reason
                        )
                        VALUES (
                            :user_id,
                            'DUPLICATE_EXPENSE',
                            'EXPENSE',
                            :transaction_id,
                            'EXPENSE',
                            :matched_transaction_id,
                            :reason
                        )
                        ON CONFLICT (
                            fraud_type,
                            transaction_source,
                            transaction_id
                        ) DO NOTHING
                        RETURNING alert_id
                    """),
                    {
                        "user_id": user_id,
                        "transaction_id": duplicate_id,
                        "matched_transaction_id": primary_id,
                        "reason": (
                            f"Possible duplicate expense: "
                            f"{group['party_name']}, "
                            f"amount {group['amount']}, "
                            f"date {group['expense_date']}"
                        ),
                    },
                )

                alert_id = result.scalar_one_or_none()

                if alert_id is not None:
                    saved_alerts.append(alert_id)

    return saved_alerts


def find_income_mismatches(user_id: int):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT
                    i.income_id,
                    i.user_id,
                    i.party_name,
                    i.amount AS recorded_income,
                    i.income_date,
                    b.transaction_id,
                    b.amount AS bank_amount,
                    b.transaction_date,
                    ABS(i.amount - b.amount) AS difference_amount
                FROM income i
                JOIN bank_transactions b
                  ON i.user_id = b.user_id
                 AND LOWER(TRIM(i.party_name)) =
                     LOWER(TRIM(b.party_name))
                 AND i.income_date = b.transaction_date
                WHERE i.user_id = :user_id
                  AND b.transaction_type = 'INCOME'
                  AND i.amount <> b.amount
                ORDER BY i.income_date DESC
            """),
            {"user_id": user_id},
        )

        return [dict(row) for row in result.mappings().all()]
