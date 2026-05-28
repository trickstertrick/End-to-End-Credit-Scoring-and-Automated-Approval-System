import sys
from database import init_db, SessionLocal, Customer, CreditApplication

def test_database_flow():
    print("Initializing database...")
    try:
        init_db()
        print("[SUCCESS] Database tables created successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        sys.exit(1)

    print("\nAdding test data...")
    db = SessionLocal()
    try:
        # 1. Test müşterisi ekle
        test_customer = Customer(
            first_name="Ahmet",
            last_name="Yılmaz",
            email="ahmet.yilmaz@example.com",
            age=34,
            annual_income=120000.0,
            employment_years=6,
            housing_status="MORTGAGE",
            credit_history_length=10,
            existing_debts=15000.0
        )
        db.add(test_customer)
        db.commit()
        db.refresh(test_customer)
        print(f"[SUCCESS] Customer created: {test_customer}")

        # 2. Test başvurusu ekle
        test_application = CreditApplication(
            customer_id=test_customer.id,
            loan_amount=50000.0,
            loan_purpose="PERSONAL",
            interest_rate=1.85,
            term_months=24,
            credit_score=750.0,
            risk_segment="Low Risk",
            approval_status="APPROVED",
            approval_probability=0.92
        )
        db.add(test_application)
        db.commit()
        db.refresh(test_application)
        print(f"[SUCCESS] Credit Application created: {test_application}")

        # 3. İlişki kontrolü
        print("\nVerifying relationships...")
        fetched_customer = db.query(Customer).filter_by(email="ahmet.yilmaz@example.com").first()
        print(f"Fetched Customer: {fetched_customer}")
        print(f"Related Applications count: {len(fetched_customer.applications)}")
        for app in fetched_customer.applications:
            print(f"  - Application ID: {app.id}, Amount: {app.loan_amount}, Status: {app.approval_status}")

        assert len(fetched_customer.applications) == 1, "Relationship mapping failed."
        print("[SUCCESS] Relationships verified successfully!")

        # Temizlik
        db.delete(fetched_customer)
        db.commit()
        print("[SUCCESS] Test data cleaned up successfully.")

    except Exception as e:
        print(f"[ERROR] Database operations failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    test_database_flow()
