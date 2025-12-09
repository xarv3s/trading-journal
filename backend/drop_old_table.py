from sqlalchemy import text
from app.core.database import engine

def drop_table():
    print("Connecting to database...")
    with engine.connect() as conn:
        try:
            # Check if table exists first
            result = conn.execute(text("SELECT to_regclass('public.account_value_candles')"))
            if not result.scalar():
                print("Table 'account_value_candles' does not exist.")
                return

            print("Dropping table 'account_value_candles'...")
            conn.execute(text("DROP TABLE account_value_candles"))
            conn.commit()
            print("Table dropped successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            conn.rollback()

if __name__ == "__main__":
    drop_table()
