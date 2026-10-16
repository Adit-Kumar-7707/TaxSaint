"""Persistence helpers for potential financial anomaly alerts."""
from sqlalchemy.orm import Session
from database_manager.models import FraudAlert

def list_alerts(db: Session, user_id: int) -> list[FraudAlert]:
    return db.query(FraudAlert).filter(FraudAlert.user_id == user_id).order_by(FraudAlert.detected_at.desc()).all()

def update_alert_status(db: Session, alert_id: int, status: str) -> FraudAlert | None:
    alert = db.get(FraudAlert, alert_id)
    if alert is None:
        return None
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert
