"""
TaxSaint Demo Data Seeder
Populates a local SQLite or PostgreSQL database with realistic demo accounts,
financial transactions, tax calculations, and potential fraud alerts for live evaluation.
"""
from datetime import date
from decimal import Decimal
from database_manager.connection import SessionLocal, init_db
from database_manager.models import User, Income, Expense, BankTransaction
from integration.api.routes.tax import calculate_tax, TaxCalculateRequest
from integration.api.routes.fraud import scan_and_save_alerts

def seed_demo_data():
    init_db()
    db = SessionLocal()
    try:
        print("🌱 Seeding TaxSaint demonstration dataset...")

        # 1. Salaried User
        rahul = db.query(User).filter(User.email == "rahul.sharma@example.com").first()
        if not rahul:
            rahul = User(
                name="Rahul Sharma",
                email="rahul.sharma@example.com",
                phone="9876543210",
                worker_type="SALARIED"
            )
            db.add(rahul)
            db.commit()
            db.refresh(rahul)
            print(f"  Created Salaried User: Rahul Sharma (ID: {rahul.user_id})")

            # Add monthly salary records
            for month in range(1, 13):
                m_str = f"{month:02d}"
                inc = Income(
                    user_id=rahul.user_id,
                    source="Infosys Technologies Ltd",
                    party_name="Infosys Technologies Ltd",
                    amount=Decimal("125000.00"),
                    income_date=date(2026 if month <= 9 else 2026, month if month <= 12 else 12, 28)
                )
                bank = BankTransaction(
                    user_id=rahul.user_id,
                    party_name="Infosys Technologies Ltd",
                    transaction_type="INCOME",
                    amount=Decimal("125000.00"),
                    transaction_date=date(2026 if month <= 9 else 2026, month if month <= 12 else 12, 28)
                )
                db.add(inc)
                db.add(bank)
            db.commit()
            print("  Added 12 months salary entries & matching bank records for Rahul.")

            # Calculate tax for Rahul
            req = TaxCalculateRequest(
                user_id=rahul.user_id,
                user_type="SALARIED",
                income=Decimal("1500000.00"),
                expenses=Decimal("0.00")
            )
            tax_res = calculate_tax(req, db)
            print(f"  Computed Tax for Rahul: Taxable ₹{tax_res['taxable_income']:.2f}, Tax ₹{tax_res['total_tax']:.2f}")

        # 2. Business User
        priya = db.query(User).filter(User.email == "priya.patel@example.com").first()
        if not priya:
            priya = User(
                name="Priya Patel",
                email="priya.patel@example.com",
                phone="9812345678",
                worker_type="BUSINESS"
            )
            db.add(priya)
            db.commit()
            db.refresh(priya)
            print(f"  Created Business User: Priya Patel (ID: {priya.user_id})")

            # Business Income
            db.add(Income(
                user_id=priya.user_id,
                source="TechCorp Global Consulting",
                party_name="TechCorp Global",
                amount=Decimal("600000.00"),
                income_date=date(2026, 5, 10)
            ))
            db.add(Income(
                user_id=priya.user_id,
                source="Apex Design Systems",
                party_name="Apex Systems",
                amount=Decimal("450000.00"),
                income_date=date(2026, 6, 15)
            ))

            # Business Expenses with a deliberate duplicate within 4 days
            db.add(Expense(
                user_id=priya.user_id,
                category="Office Supplies",
                party_name="Office Depot India",
                amount=Decimal("8500.00"),
                expense_date=date(2026, 5, 12)
            ))
            db.add(Expense(
                user_id=priya.user_id,
                category="Office Supplies",
                party_name="Office Depot India",
                amount=Decimal("8500.00"),
                expense_date=date(2026, 5, 15)  # Duplicate! 3 days later
            ))
            db.add(Expense(
                user_id=priya.user_id,
                category="Cloud Infrastructure",
                party_name="AWS Cloud Hosting",
                amount=Decimal("34500.00"),
                expense_date=date(2026, 6, 20)
            ))

            # Bank transactions with an income mismatch
            # Bank shows only 550,000 received instead of recorded 600,000
            db.add(BankTransaction(
                user_id=priya.user_id,
                party_name="TechCorp Global",
                transaction_type="INCOME",
                amount=Decimal("550000.00"),
                transaction_date=date(2026, 5, 11)
            ))
            db.commit()
            print("  Added business revenue, expenses, and deliberate anomalies for Priya.")

            # Scan and persist anomaly alerts
            alerts = scan_and_save_alerts(db, priya.user_id)
            print(f"  Detected & persisted {alerts['summary'].get('new_alerts_saved', 0)} anomaly alert(s) for Priya.")

            # Calculate tax for Priya
            req = TaxCalculateRequest(
                user_id=priya.user_id,
                user_type="BUSINESS",
                income=Decimal("1050000.00"),
                expenses=Decimal("51500.00")
            )
            tax_res = calculate_tax(req, db)
            print(f"  Computed Tax for Priya: Taxable ₹{tax_res['taxable_income']:.2f}, Tax ₹{tax_res['total_tax']:.2f}")

        print("\n✅ Seed complete! Evaluation demo users ready:")
        print("   1. Rahul Sharma (Salaried) -> rahul.sharma@example.com (User ID: 1)")
        print("   2. Priya Patel (Business)  -> priya.patel@example.com  (User ID: 2)")

    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
