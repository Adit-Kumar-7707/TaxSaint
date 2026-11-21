"""Validated request bodies shared by the FastAPI route modules."""
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

class RequestModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

# --- User & Auth Schemas ---

class UserCreate(RequestModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=6, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    user_type: Literal["salaried", "business", "SALARIED", "BUSINESS"] = Field(
        validation_alias=AliasChoices("userType", "user_type", "worker_type")
    )

class UserLogin(RequestModel):
    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=100)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserUpdate(RequestModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    user_type: Literal["salaried", "business", "SALARIED", "BUSINESS"] = Field(
        validation_alias=AliasChoices("userType", "user_type", "worker_type")
    )

# --- Financial & Transaction Schemas ---

class IncomeCreate(RequestModel):
    user_id: int = Field(gt=0, validation_alias=AliasChoices("userId", "user_id"))
    source: str = Field(min_length=1, max_length=50)
    party_name: str | None = Field(default=None, max_length=100, validation_alias=AliasChoices("partyName", "party_name"))
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    income_date: date = Field(validation_alias=AliasChoices("incomeDate", "income_date", "date"))

class ExpenseCreate(RequestModel):
    user_id: int = Field(gt=0, validation_alias=AliasChoices("userId", "user_id"))
    category: str = Field(min_length=1, max_length=50)
    party_name: str = Field(min_length=1, max_length=100, validation_alias=AliasChoices("partyName", "party_name"))
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    expense_date: date = Field(validation_alias=AliasChoices("expenseDate", "expense_date", "date"))

class BankTransactionCreate(RequestModel):
    user_id: int = Field(gt=0, validation_alias=AliasChoices("userId", "user_id"))
    party_name: str | None = Field(default=None, max_length=100, validation_alias=AliasChoices("partyName", "party_name"))
    transaction_type: Literal["INCOME", "EXPENSE", "income", "expense"] = Field(
        validation_alias=AliasChoices("transactionType", "transaction_type")
    )
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    transaction_date: date = Field(validation_alias=AliasChoices("transactionDate", "transaction_date", "date"))

# --- Tax & Anomaly Schemas ---

class TaxCalculateRequest(RequestModel):
    user_id: int = Field(gt=0, validation_alias=AliasChoices("userId", "user_id"))
    user_type: str | None = Field(default=None, validation_alias=AliasChoices("userType", "user_type", "worker_type"))
    income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    expenses: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    salary: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    other_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2, validation_alias=AliasChoices("otherIncome", "other_income"))
    business_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2, validation_alias=AliasChoices("businessIncome", "business_income"))
    business_expenses: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2, validation_alias=AliasChoices("businessExpenses", "business_expenses"))
    deductions: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)

class AlertStatusUpdate(RequestModel):
    status: Literal["NEEDS_VERIFICATION", "VERIFIED", "DISMISSED"]
