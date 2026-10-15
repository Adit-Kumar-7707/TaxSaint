"""TaxSaint API entry point."""
from datetime import date
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from database_manager.connection import engine
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
