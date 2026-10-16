"""Database query helpers for financial records and summaries."""
from sqlalchemy import func
from sqlalchemy.orm import Session
from database_manager.models import BankTransaction, Expense, Income

def get_financial_totals(db: Session, user_id: int) -> dict[str, float]:
    income = db.query(func.coalesce(func.sum(Income.amount), 0)).filter(Income.user_id == user_id).scalar() or 0
    expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == user_id).scalar() or 0
    return {"income": float(income), "expenses": float(expenses), "netPosition": float(income - expenses)}

def list_user_transactions(db: Session, user_id: int) -> tuple[list[Income], list[Expense], list[BankTransaction]]:
    return (
        db.query(Income).filter(Income.user_id == user_id).order_by(Income.income_date, Income.income_id).all(),
        db.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.expense_date, Expense.expense_id).all(),
        db.query(BankTransaction).filter(BankTransaction.user_id == user_id).order_by(BankTransaction.transaction_date, BankTransaction.transaction_id).all(),
    )
