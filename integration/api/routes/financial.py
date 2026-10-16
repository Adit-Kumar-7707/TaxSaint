"""Income, expense, bank-transaction, and financial-summary endpoints."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from database_manager.connection import get_db
from database_manager.models import BankTransaction, Expense, Income, User
from database_manager.repositories.financial_repository import get_financial_totals
from integration.api.schemas.requests import BankTransactionCreate, ExpenseCreate, IncomeCreate

router = APIRouter(prefix="/api/financial", tags=["financial"])

def _require_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Create the user before adding financial records.")
    return user

def _record_fraud_scan(db: Session, user_id: int) -> None:
    """Refresh anomaly alerts after a financial record is added; never confirms fraud."""
    try:
        from integration.api.routes.fraud import scan_and_save_alerts
        scan_and_save_alerts(db, user_id)
    except Exception:
        # The financial record is valid even if the optional scan fails; the scan endpoint can be retried.
        db.rollback()

@router.post("/income", status_code=status.HTTP_201_CREATED)
def create_income(payload: IncomeCreate, db: Session = Depends(get_db)):
    _require_user(db, payload.user_id)
    record = Income(user_id=payload.user_id, source=payload.source.strip(),
                    party_name=(payload.party_name or payload.source).strip(),
                    amount=payload.amount, income_date=payload.income_date)
    db.add(record)
    db.commit()
    db.refresh(record)
    _record_fraud_scan(db, payload.user_id)
    return {"income_id": record.income_id, "user_id": record.user_id, "source": record.source,
            "party_name": record.party_name, "amount": float(record.amount), "income_date": record.income_date.isoformat()}

@router.post("/expenses", status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    _require_user(db, payload.user_id)
    record = Expense(user_id=payload.user_id, category=payload.category.strip(),
                     party_name=payload.party_name.strip(), amount=payload.amount,
                     expense_date=payload.expense_date)
    db.add(record)
    db.commit()
    db.refresh(record)
    _record_fraud_scan(db, payload.user_id)
    return {"expense_id": record.expense_id, "user_id": record.user_id, "category": record.category,
            "party_name": record.party_name, "amount": float(record.amount), "expense_date": record.expense_date.isoformat()}

@router.post("/bank-transactions", status_code=status.HTTP_201_CREATED)
def create_bank_transaction(payload: BankTransactionCreate, db: Session = Depends(get_db)):
    _require_user(db, payload.user_id)
    record = BankTransaction(user_id=payload.user_id, party_name=payload.party_name,
                             transaction_type=payload.transaction_type.upper(), amount=payload.amount,
                             transaction_date=payload.transaction_date)
    db.add(record)
    db.commit()
    db.refresh(record)
    _record_fraud_scan(db, payload.user_id)
    return {"transaction_id": record.transaction_id, "user_id": record.user_id,
            "party_name": record.party_name, "transaction_type": record.transaction_type,
            "amount": float(record.amount), "transaction_date": record.transaction_date.isoformat()}

@router.get("/summary/{user_id}")
def financial_summary(user_id: int, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    totals = get_financial_totals(db, user_id)
    return totals

@router.get("/income/{user_id}")
def list_income(user_id: int, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    rows = db.query(Income).filter(Income.user_id == user_id).order_by(Income.income_date.desc()).all()
    return [{"income_id": r.income_id, "source": r.source, "party_name": r.party_name,
             "amount": float(r.amount), "income_date": r.income_date.isoformat()} for r in rows]

@router.get("/expenses/{user_id}")
def list_expenses(user_id: int, db: Session = Depends(get_db)):
    _require_user(db, user_id)
    rows = db.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.expense_date.desc()).all()
    return [{"expense_id": r.expense_id, "category": r.category, "party_name": r.party_name,
             "amount": float(r.amount), "expense_date": r.expense_date.isoformat()} for r in rows]

@router.post("/upload")
async def upload_statement(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Parse CSV or Excel statements and ingest transactions directly into database."""
    _require_user(db, user_id)
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    from data_input.importers.csv_importer import process_file_stream, ImporterError
    try:
        summary = process_file_stream(contents, file.filename or "statement.csv", user_id)
        _record_fraud_scan(db, user_id)
        return {
            "ok": summary.status in ("success", "no_new_records"),
            "status": summary.status,
            "filename": file.filename,
            "transaction_type": summary.transaction_type.value if hasattr(summary.transaction_type, "value") else str(summary.transaction_type),
            "total_rows": summary.total_rows,
            "imported": summary.sent_count,
            "duplicates": summary.duplicate_count,
            "invalid": summary.invalid_count,
            "message": summary.message or f"Successfully imported {summary.sent_count} records."
        }
    except ImporterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process statement: {exc}") from exc
