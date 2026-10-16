"""Smoke tests for the FastAPI-to-database/tax/fraud integration."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile

# Use an isolated local database for tests; never connect to a developer's Supabase DB.
_test_db = Path(tempfile.gettempdir()) / f"taxsaint-api-tests-{os.getpid()}.db"
_test_db.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db}"

from fastapi.testclient import TestClient  # noqa: E402
from database_manager.connection import Base, engine  # noqa: E402
from integration.api.main import app  # noqa: E402


def test_api_end_to_end_flow():
    """Create a user, persist transactions, calculate tax, and review alerts."""
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

        response = client.post("/api/users", json={
            "name": "Integration Test User",
            "email": "integration-test@example.com",
            "phone": "9000000000",
            "userType": "business",
        })
        assert response.status_code == 201, response.text
        user = response.json()
        user_id = user["id"]
        assert user["worker_type"] == "BUSINESS"

        response = client.post("/api/financial/income", json={
            "userId": user_id, "source": "Acme Ltd", "amount": 100000,
            "incomeDate": "2026-10-01",
        })
        assert response.status_code == 201, response.text

        # Mark the initial missing-credit alert as reviewed; a later bank import
        # should reopen it because the evidence and difference amount change.
        initial_alerts = client.get(f"/api/fraud/alerts/{user_id}").json()["alerts"]
        initial_income_alert = next(alert for alert in initial_alerts if alert["type"] == "INCOME_MISMATCH")
        reviewed = client.put(f"/api/fraud/alerts/{initial_income_alert['id']}/status", json={"status": "VERIFIED"})
        assert reviewed.status_code == 200

        for day in ("2026-10-02", "2026-10-05"):
            response = client.post("/api/financial/expenses", json={
                "userId": user_id, "partyName": "Office Supply Co", "category": "Supplies",
                "amount": 5000, "expenseDate": day,
            })
            assert response.status_code == 201, response.text

        response = client.post("/api/financial/bank-transactions", json={
            "userId": user_id, "partyName": "Acme Ltd", "transactionType": "INCOME",
            "amount": 90000, "transactionDate": "2026-10-02",
        })
        assert response.status_code == 201, response.text

        summary = client.get(f"/api/financial/summary/{user_id}")
        assert summary.status_code == 200
        assert summary.json() == {"income": 100000.0, "expenses": 10000.0, "netPosition": 90000.0}

        tax = client.post("/api/tax/calculate", json={
            "userId": user_id, "userType": "business", "businessIncome": 100000,
            "businessExpenses": 10000,
        })
        assert tax.status_code == 200, tax.text
        assert tax.json()["taxableIncome"] == 90000.0
        assert tax.json()["totalTax"] == 0.0
        assert client.get(f"/api/tax/result/{user_id}").json()["totalTax"] == 0.0

        alerts_response = client.get(f"/api/fraud/alerts/{user_id}")
        assert alerts_response.status_code == 200
        alerts = alerts_response.json()["alerts"]
        assert any(alert["type"] == "DUPLICATE_EXPENSE" for alert in alerts)
        assert any(alert["type"] == "INCOME_MISMATCH" for alert in alerts)

        # The late bank credit should update the original alert to the true amount difference.
        income_alert = next(alert for alert in alerts if alert["type"] == "INCOME_MISMATCH")
        assert income_alert["matched_source"] == "BANK"
        assert income_alert["difference_amount"] == 10000.0
        assert income_alert["status"] == "NEEDS_VERIFICATION"

        updated = client.put(f"/api/fraud/alerts/{income_alert['id']}/status", json={"status": "VERIFIED"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "VERIFIED"

        # Re-running the same scan must not reset a status if the evidence is unchanged.
        refreshed = client.post(f"/api/fraud/scan/{user_id}")
        assert refreshed.status_code == 200
        latest_alerts = client.get(f"/api/fraud/alerts/{user_id}").json()["alerts"]
        latest_income_alert = next(alert for alert in latest_alerts if alert["type"] == "INCOME_MISMATCH")
        assert latest_income_alert["status"] == "VERIFIED"

        duplicate_email = client.post("/api/users", json={
            "name": "Duplicate", "email": "integration-test@example.com", "userType": "business"
        })
        assert duplicate_email.status_code == 409
