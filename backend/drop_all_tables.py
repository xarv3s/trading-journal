import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from sqlalchemy import inspect, text

def drop_all_tables():
    print("WARNING: This will DROP ALL TABLES from the database schema.")
    confirm = input("Are you sure? (type 'yes' to confirm): ")
    if confirm != 'yes':
        print("Aborted.")
        return

    db = SessionLocal()
    try:
        inspector = inspect(db.get_bind())
        tables = inspector.get_table_names()
        
        if not tables:
            print("No tables found to drop.")
            return

        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Disable foreign key checks for SQLite to avoid constraint errors during drop
        if 'sqlite' in str(engine.url):
            db.execute(text("PRAGMA foreign_keys = OFF"))
            
        for table in tables:
            print(f"Dropping table: {table}...")
            db.execute(text(f"DROP TABLE IF EXISTS {table}"))
            
        if 'sqlite' in str(engine.url):
            db.execute(text("PRAGMA foreign_keys = ON"))
            
        db.commit()
        print("All tables dropped successfully.")
        
    except Exception as e:
        print(f"Error dropping tables: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        # Force mode logic
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            tables = inspector.get_table_names()
            if tables:
                if 'sqlite' in str(engine.url):
                    db.execute(text("PRAGMA foreign_keys = OFF"))
                for table in tables:
                    print(f"Dropping table: {table}...")
                    db.execute(text(f"DROP TABLE IF EXISTS {table}"))
                if 'sqlite' in str(engine.url):
                    db.execute(text("PRAGMA foreign_keys = ON"))
                db.commit()
                print("All tables dropped successfully.")
            else:
                print("No tables found.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            db.close()
    else:
        drop_all_tables()
