import requests
import time
from sqlalchemy import text
from app.core.database import engine

API_URL = "http://localhost:8000/api/v1/analytics/aggregate"

def verify_aggregation():
    print("Triggering aggregation...")
    try:
        response = requests.post(API_URL)
        if response.status_code == 200:
            print("Aggregation triggered successfully.")
            print("Response:", response.json())
        else:
            print(f"Failed to trigger aggregation. Status: {response.status_code}")
            print("Response:", response.text)
            return
    except Exception as e:
        print(f"Error triggering aggregation: {e}")
        return

    print("Verifying database content...")
    with engine.connect() as conn:
        daily_count = conn.execute(text("SELECT count(*) FROM daily_account_values")).scalar()
        weekly_count = conn.execute(text("SELECT count(*) FROM weekly_account_values")).scalar()
        
        print(f"Daily records: {daily_count}")
        print(f"Weekly records: {weekly_count}")
        
        if daily_count > 0 and weekly_count > 0:
            print("Verification SUCCESS: Tables populated.")
        else:
            print("Verification FAILED: Tables empty.")

if __name__ == "__main__":
    verify_aggregation()
