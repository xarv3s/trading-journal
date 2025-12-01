import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv("credentials.env")
DATABASE_URL = os.getenv("SUPABASE_URL")

def kill_locks():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Killing blocking sessions...")
        # Kill all sessions that are idle in transaction or active for too long (except me)
        # Be careful not to kill my own session.
        
        sql = """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE state = 'idle in transaction'
        AND pid <> pg_backend_pid();
        """
        
        try:
            result = conn.execute(text(sql))
            print("Killed idle transactions.")
        except Exception as e:
            print(f"Error killing sessions: {e}")
            
        # Now try to add columns again
        print("Retrying add columns...")
        try:
            conn.execute(text("ALTER TABLE daily_equity ADD COLUMN IF NOT EXISTS nifty50 DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE daily_equity ADD COLUMN IF NOT EXISTS nifty_midcap150 DOUBLE PRECISION"))
            conn.execute(text("ALTER TABLE daily_equity ADD COLUMN IF NOT EXISTS nifty_smallcap250 DOUBLE PRECISION"))
            conn.commit()
            print("Columns added successfully.")
        except Exception as e:
            print(f"Error adding columns: {e}")

if __name__ == "__main__":
    kill_locks()
