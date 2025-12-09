from sqlalchemy import text
from app.core.database import engine

def verify_migration():
    print("Connecting to database...")
    with engine.connect() as conn:
        try:
            count_old = conn.execute(text("SELECT count(*) FROM account_value_candles")).scalar()
            count_new = conn.execute(text("SELECT count(*) FROM account_values")).scalar()
            
            print(f"Rows in 'account_value_candles': {count_old}")
            print(f"Rows in 'account_values': {count_new}")
            
            if count_new >= count_old:
                print("Verification SUCCESS: New table has all data.")
            else:
                print("Verification FAILED: New table has fewer rows.")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    verify_migration()
