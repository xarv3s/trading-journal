import sqlite3
import os

DB_PATH = "../data/trading_journal.db"

def list_tables():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables found:")
    for table in tables:
        print(f"- {table[0]}")
        
    conn.close()

if __name__ == "__main__":
    list_tables()
