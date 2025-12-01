from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("credentials.env")

# Create the database directory if it doesn't exist (keeping this for safety, though not used for Supabase)
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = os.getenv("SUPABASE_URL")

if not DATABASE_URL:
    # Fallback to local SQLite if SUPABASE_URL is not set (or raise error)
    print("Warning: SUPABASE_URL not found, falling back to local SQLite.")
    DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'trading_journal.db')}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Postgres connection
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
