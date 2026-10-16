"""Potential anomaly scan and alert status endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database_manager.connection import get_db
from database_manager.models import BankTransaction, Expense, FraudAlert, Income, User
from database_manager.repositories.fraud_repository import list_alerts, update_alert_status
from integration.api.schemas.requests import AlertStatusUpdate
from tax_calculation.fraud_engine.fraud_detector import scan_transactions

router = APIRouter(prefix="/api/fraud", tags=["fraud"])

def _as_dict(row, source: str) -> dict:
    if source == "EXPENSE":
        return {"expense_id": row.expense_id, "user_id": row.user_id, "party_name": row.party_name,
                "amount": row.amount, "expense_date": row.expense_date}
    if source == "INCOME":
        return {"income_id": row.income_id, "user_id": row.user_id, "party_name": row.party_name,
                "source": row.source, "amount": row.amount, "income_date": row.income_date}
    return {"transaction_id": row.transaction_id, "user_id": row.user_id, "party_name": row.party_name,
            "transaction_type": row.transaction_type, "amount": row.amount, "transaction_date": row.transaction_date}

def scan_and_save_alerts(db: Session, user_id: int) -> dict:
    """Run deterministic rules and persist new alerts without resetting existing statuses."""
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    incomes = db.query(Income).filter(Income.user_id == user_id).all()
    bank_rows = db.query(BankTransaction).filter(BankTransaction.user_id == user_id).all()
    result = scan_transactions(
        expenses=[_as_dict(row, "EXPENSE") for row in expenses],
        income=[_as_dict(row, "INCOME") for row in incomes],
        bank_transactions=[_as_dict(row, "BANK") for row in bank_rows],
    )
    saved = 0
    for item in result["alerts"]:
        exists = db.query(FraudAlert).filter(
            FraudAlert.fraud_type == item["fraud_type"],
            FraudAlert.transaction_source == item["transaction_source"],
            FraudAlert.transaction_id == item["transaction_id"],
        ).first()
        if exists is None:
            db.add(FraudAlert(**item))
            saved += 1
        else:
            # A later bank import can change a previous "missing credit" alert into
            # an amount mismatch. Refresh its evidence; if the evidence changed,
            # send it back for verification rather than retaining a stale status.
            evidence_changed = (
                exists.matched_source != item.get("matched_source")
                or exists.matched_transaction_id != item.get("matched_transaction_id")
                or round(float(exists.difference_amount or 0), 2) != round(float(item.get("difference_amount") or 0), 2)
                or exists.reason != item.get("reason")
            )
            exists.matched_source = item.get("matched_source")
            exists.matched_transaction_id = item.get("matched_transaction_id")
            exists.difference_amount = item.get("difference_amount")
            exists.reason = item["reason"]
            if evidence_changed:
                exists.status = "NEEDS_VERIFICATION"
    db.commit()
    return {"ok": result["ok"], "summary": {**result["summary"], "new_alerts_saved": saved}, "errors": result["errors"]}

@router.post("/scan/{user_id}")
def scan_user_transactions(user_id: int, db: Session = Depends(get_db)):
    return scan_and_save_alerts(db, user_id)

@router.get("/alerts/{user_id}")
def get_user_alerts(user_id: int, db: Session = Depends(get_db)):
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found.")
    rows = list_alerts(db, user_id)
    serialized = []
    for row in rows:
        # Resolve the party name from the source table for the alert card UI.
        source_record = None
        if row.transaction_source == "EXPENSE":
            source_record = db.get(Expense, row.transaction_id)
        elif row.transaction_source == "INCOME":
            source_record = db.get(Income, row.transaction_id)
        elif row.transaction_source == "BANK":
            source_record = db.get(BankTransaction, row.transaction_id)
        party_name = getattr(source_record, "party_name", None)
        serialized.append({
            "id": row.alert_id, "alert_id": row.alert_id, "user_id": row.user_id,
            "type": row.fraud_type, "alertType": row.fraud_type, "fraud_type": row.fraud_type,
            "transaction_source": row.transaction_source, "transaction_id": row.transaction_id,
            "matched_source": row.matched_source, "matched_transaction_id": row.matched_transaction_id,
            "difference_amount": float(row.difference_amount or 0), "amount": float(row.difference_amount or 0),
            "partyName": party_name, "reason": row.reason, "message": row.reason, "status": row.status,
            "detected_at": row.detected_at.isoformat() if row.detected_at else None,
        })
    return {"alerts": serialized}

@router.put("/alerts/{alert_id}/status")
def change_alert_status(alert_id: int, payload: AlertStatusUpdate, db: Session = Depends(get_db)):
    alert = update_alert_status(db, alert_id, payload.status)
    if alert is None:
        raise HTTPException(status_code=404, detail="Fraud alert not found.")
    return {"id": alert.alert_id, "alert_id": alert.alert_id, "status": alert.status}
