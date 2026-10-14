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