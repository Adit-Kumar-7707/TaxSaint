"""TaxSaint API entry point."""
from datetime import date
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from database_manager.connection import engine
from database_manager.repositories.fraud_repository import (
    find_duplicate_expenses,
    save_duplicate_alerts,
)
from database_manager.repositories.fraud_repository import (
    find_duplicate_expenses,
    save_duplicate_alerts,
    find_income_mismatches,
)
from database_manager.repositories.fraud_repository import (
    find_duplicate_expenses,
    save_duplicate_alerts,
    find_income_mismatches,
    save_income_mismatch_alerts,
)
import json
import subprocess
from pathlib import Path



app = FastAPI(title="TaxSaint API")


@app.get("/")
def home():
    return {"message": "TaxSaint API is running"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(inspect(engine).dialect.statement_compiler(
                inspect(engine).dialect, None
            ).statement) if False else connection.exec_driver_sql("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }
    
class IncomeCreate(BaseModel):
    user_id: int
    source: str = Field(min_length=1, max_length=50)
    party_name: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    income_date: date

@app.post("/income", status_code=201)
def create_income(income: IncomeCreate):
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO income
                    (user_id, source, party_name, amount, income_date)
                    VALUES
                    (:user_id, :source, :party_name, :amount, :income_date)
                    RETURNING income_id
                """),
                {
                    "user_id": income.user_id,
                    "source": income.source,
                    "party_name": income.party_name,
                    "amount": income.amount,
                    "income_date": income.income_date,
                },
            )

            income_id = result.scalar_one()

        return {
            "message": "Income added successfully",
            "income_id": income_id,
        }

    except IntegrityError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id or income data",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to save income",
        ) from error
    
@app.get("/income")
def get_income(user_id: int):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT income_id, user_id, source, party_name,
                           amount, income_date
                    FROM income
                    WHERE user_id = :user_id
                    ORDER BY income_date DESC
                """),
                {"user_id": user_id},
            )

            records = result.mappings().all()

        return {"income": [dict(row) for row in records]}

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch income records",
        ) from error

@app.get("/expenses")
def get_expenses(user_id: int):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT expense_id, user_id, category,
                           party_name, amount, expense_date
                    FROM expenses
                    WHERE user_id = :user_id
                    ORDER BY expense_date DESC
                """),
                {"user_id": user_id},
            )

            records = result.mappings().all()

        return {"expenses": [dict(row) for row in records]}

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch expense records",
        ) from error


class ExpenseCreate(BaseModel):
    user_id: int
    category: str = Field(min_length=1, max_length=50)
    party_name: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    expense_date: date


@app.post("/expenses", status_code=201)
def create_expense(expense: ExpenseCreate):
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO expenses
                    (user_id, category, party_name, amount, expense_date)
                    VALUES
                    (:user_id, :category, :party_name, :amount, :expense_date)
                    RETURNING expense_id
                """),
                {
                    "user_id": expense.user_id,
                    "category": expense.category,
                    "party_name": expense.party_name,
                    "amount": expense.amount,
                    "expense_date": expense.expense_date,
                },
            )

            expense_id = result.scalar_one()

        return {
            "message": "Expense added successfully",
            "expense_id": expense_id,
        }

    except IntegrityError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id or expense data",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to save expense",
        ) from error

class BankTransactionCreate(BaseModel):
    user_id: int
    party_name: str = Field(min_length=1, max_length=100)
    transaction_type: str
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    transaction_date: date


@app.post("/bank-transactions", status_code=201)
def create_bank_transaction(transaction: BankTransactionCreate):
    transaction_type = transaction.transaction_type.upper()

    if transaction_type not in ("INCOME", "EXPENSE"):
        raise HTTPException(
            status_code=422,
            detail="transaction_type must be INCOME or EXPENSE",
        )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO bank_transactions
                    (user_id, party_name, transaction_type, amount, transaction_date)
                    VALUES
                    (:user_id, :party_name, :transaction_type, :amount, :transaction_date)
                    RETURNING transaction_id
                """),
                {
                    "user_id": transaction.user_id,
                    "party_name": transaction.party_name,
                    "transaction_type": transaction_type,
                    "amount": transaction.amount,
                    "transaction_date": transaction.transaction_date,
                },
            )

            transaction_id = result.scalar_one()

        return {
            "message": "Bank transaction added successfully",
            "transaction_id": transaction_id,
        }

    except IntegrityError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id or transaction data",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to save bank transaction",
        ) from error


@app.get("/bank-transactions")
def get_bank_transactions(user_id: int):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT transaction_id, user_id, party_name,
                           transaction_type, amount, transaction_date
                    FROM bank_transactions
                    WHERE user_id = :user_id
                    ORDER BY transaction_date DESC
                """),
                {"user_id": user_id},
            )

            records = result.mappings().all()

        return {
            "bank_transactions": [dict(row) for row in records]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch bank transactions",
        ) from error


@app.get("/fraud/duplicate-expenses")
def get_duplicate_expenses(user_id: int):
    try:
        duplicates = find_duplicate_expenses(user_id)
        return {
            "user_id": user_id,
            "duplicate_groups": duplicates,
            "count": len(duplicates),
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to detect duplicate expenses",
        ) from error


@app.post("/fraud/duplicate-expenses/scan")
def scan_duplicate_expenses(user_id: int):
    try:
        saved_alert_ids = save_duplicate_alerts(user_id)

        return {
            "message": "Duplicate expense scan completed",
            "user_id": user_id,
            "alerts_created": len(saved_alert_ids),
            "alert_ids": saved_alert_ids,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to save duplicate expense alerts",
        ) from error


@app.get("/fraud/income-mismatches")
def get_income_mismatches(user_id: int):
    try:
        mismatches = find_income_mismatches(user_id)

        return {
            "user_id": user_id,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to detect income mismatches",
        ) from error


@app.post("/fraud/income-mismatches/scan")
def scan_income_mismatches(user_id: int):
    try:
        alert_ids = save_income_mismatch_alerts(user_id)

        return {
            "message": "Income mismatch scan completed",
            "user_id": user_id,
            "alerts_created": len(alert_ids),
            "alert_ids": alert_ids,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to save income mismatch alerts",
        ) from error


@app.get("/fraud/alerts")
def get_fraud_alerts(user_id: int):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        alert_id,
                        user_id,
                        fraud_type,
                        transaction_source,
                        transaction_id,
                        matched_source,
                        matched_transaction_id,
                        difference_amount,
                        reason,
                        status,
                        detected_at
                    FROM fraud_alerts
                    WHERE user_id = :user_id
                    ORDER BY detected_at DESC
                """),
                {"user_id": user_id},
            )

            alerts = result.mappings().all()

        return {
            "user_id": user_id,
            "count": len(alerts),
            "alerts": [dict(alert) for alert in alerts],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch fraud alerts",
        ) from error


class FraudAlertStatusUpdate(BaseModel):
    status: str


@app.patch("/fraud/alerts/{alert_id}")
def update_fraud_alert_status(
    alert_id: int,
    update: FraudAlertStatusUpdate,
    user_id: int,
):
    if update.status not in ("VERIFIED", "DISMISSED"):
        raise HTTPException(
            status_code=422,
            detail="Status must be VERIFIED or DISMISSED",
        )

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    UPDATE fraud_alerts
                    SET status = :status
                    WHERE alert_id = :alert_id
                      AND user_id = :user_id
                    RETURNING alert_id, user_id, fraud_type, status
                """),
                {
                    "status": update.status,
                    "alert_id": alert_id,
                    "user_id": user_id,
                },
            )

            alert = result.mappings().one_or_none()

        if alert is None:
            raise HTTPException(
                status_code=404,
                detail="Fraud alert not found",
            )

        return {
            "message": "Fraud alert status updated",
            "alert": dict(alert),
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to update fraud alert",
        ) from error


@app.post("/tax/calculate")
def calculate_user_tax(user_id: int, financial_year: str = "2026-27"):
    # Financial year ki date range
    year_ranges = {
        "2026-27": (date(2026, 4, 1), date(2027, 4, 1)),
    }

    if financial_year not in year_ranges:
        raise HTTPException(
            status_code=400,
            detail="Unsupported financial year",
        )

    start_date, end_date = year_ranges[financial_year]

    try:
        with engine.connect() as connection:
            # User ka worker type
            user = connection.execute(
                text("""
                    SELECT worker_type
                    FROM users
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id},
            ).mappings().one_or_none()

            if user is None:
                raise HTTPException(status_code=404, detail="User not found")

            # Demo tax rules
            rules = connection.execute(
                text("""
                    SELECT standard_deduction, rebate_limit, cess_rate
                    FROM tax_rules
                    WHERE financial_year = :financial_year
                      AND regime = 'NEW'
                """),
                {"financial_year": financial_year},
            ).mappings().one_or_none()

            if rules is None:
                raise HTTPException(
                    status_code=404,
                    detail="Tax rules not found for this financial year",
                )

            # Tax slabs
            slabs = connection.execute(
                text("""
                    SELECT lower_limit, upper_limit, rate
                    FROM tax_slabs
                    ORDER BY lower_limit
                """)
            ).mappings().all()

            if not slabs:
                raise HTTPException(status_code=500, detail="Tax slabs not found")

            # Financial year ke andar total income
            income = connection.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM income
                    WHERE user_id = :user_id
                      AND income_date >= :start_date
                      AND income_date < :end_date
                """),
                {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            ).scalar_one()

            # Financial year ke andar total expenses
            expenses = connection.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM expenses
                    WHERE user_id = :user_id
                      AND expense_date >= :start_date
                      AND expense_date < :end_date
                """),
                {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            ).scalar_one()

        # C++ engine ke liye input taiyar karo
        input_lines = [
            f"RULE|standard_deduction|{rules['standard_deduction']}",
            f"RULE|rebate_limit|{rules['rebate_limit']}",
            f"RULE|cess_rate|{rules['cess_rate']}",
        ]

        for slab in slabs:
            upper = (
                str(slab["upper_limit"])
                if slab["upper_limit"] is not None
                else ""
            )
            input_lines.append(
                f"SLAB|{slab['lower_limit']}|{upper}|{slab['rate']}"
            )

        input_lines.append(
            f"USER|{user_id}|{user['worker_type']}|{income}|{expenses}"
        )

        engine_path = (
            Path(__file__).resolve().parents[2]
            / "tax_calculation"
            / "tax_engine"
            / "calculatetax"
        )

        if not engine_path.is_file():
            raise HTTPException(
                status_code=500,
                detail="C++ tax engine executable not found. Compile it first.",
            )

        result = subprocess.run(
            [str(engine_path)],
            input="\n".join(input_lines) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=422,
                detail="C++ tax engine rejected the input or rules",
            )

        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=500,
                detail="Invalid response from C++ tax engine",
            ) from error

        if not output.get("ok") or not output.get("results"):
            raise HTTPException(
                status_code=422,
                detail="Tax calculation failed",
            )

        tax = output["results"][0]

        # Result database mein save karo
        with engine.begin() as connection:
            saved = connection.execute(
                text("""
                    INSERT INTO tax_results (
                        user_id, gross_income, expenses, taxable_income,
                        tax_before_cess, cess, total_tax
                    )
                    VALUES (
                        :user_id, :gross_income, :expenses, :taxable_income,
                        :tax_before_cess, :cess, :total_tax
                    )
                    RETURNING result_id, calculated_at
                """),
                {
                    "user_id": user_id,
                    "gross_income": tax["gross_income"],
                    "expenses": tax["expenses"],
                    "taxable_income": tax["taxable_income"],
                    "tax_before_cess": tax["tax_before_cess"],
                    "cess": tax["cess"],
                    "total_tax": tax["total_tax"],
                },
            ).mappings().one()

        return {
            "message": "Tax calculated and saved successfully",
            "financial_year": financial_year,
            "regime": "NEW",
            "tax": tax,
            "result_id": saved["result_id"],
            "calculated_at": saved["calculated_at"],
            "notice": "Demo tax rules only; verify rules before real tax use.",
        }

    except HTTPException:
        raise
    except subprocess.TimeoutExpired as error:
        raise HTTPException(
            status_code=500,
            detail="C++ tax engine timed out",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to calculate and save tax",
        ) from error


@app.get("/tax/results")
def get_tax_results(user_id: int):
    try:
        with engine.connect() as connection:
            results = connection.execute(
                text("""
                    SELECT
                        result_id,
                        user_id,
                        gross_income,
                        expenses,
                        taxable_income,
                        tax_before_cess,
                        cess,
                        total_tax,
                        calculated_at
                    FROM tax_results
                    WHERE user_id = :user_id
                    ORDER BY calculated_at DESC
                """),
                {"user_id": user_id},
            ).mappings().all()

        return {
            "user_id": user_id,
            "count": len(results),
            "results": [dict(row) for row in results],
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch tax results",
        ) from error
