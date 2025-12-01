import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def test_connection():
    print("\n--- Testing Configuration & Connection ---")
    
    # 1. Test Env Loading
    load_dotenv("credentials.env")
    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    supabase_url = os.getenv("SUPABASE_URL")
    
    print(f"API Key present: {bool(api_key)}")
    print(f"API Secret present: {bool(api_secret)}")
    print(f"Supabase URL present: {bool(supabase_url)}")
    
    assert api_key is not None
    assert api_secret is not None
    assert supabase_url is not None
    
    # 2. Test DB Connection
    try:
        engine = create_engine(supabase_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database Connection Successful!")
            print(f"Result: {result.fetchone()}")
    except Exception as e:
        print(f"Database Connection Failed: {e}")
        exit(1)

if __name__ == "__main__":
    test_connection()
