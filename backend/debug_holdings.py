import pandas as pd
from app.core.database import SessionLocal
from app.models.all_models import OpenTrade
from app.services.kite_service import KiteClient
from app.core.config import get_settings

db = SessionLocal()

print("--- Checking DB Content ---")
trades = db.query(OpenTrade).all()
print(f"Total Open Trades in DB: {len(trades)}")
for t in trades:
    print(f"Symbol: {t.symbol}, Type: {t.type}, Product: {t.product}, Qty: {t.qty}")

print("\n--- Checking Zerodha Holdings ---")
settings = get_settings()
token = KiteClient.load_access_token()
if token:
    kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
    try:
        holdings = kite.fetch_holdings()
        print(f"Holdings fetched: {len(holdings)}")
        if not holdings.empty:
            print("First holding full data:")
            print(holdings.iloc[0].to_dict())
        else:
            print("Holdings DataFrame is empty.")
    except Exception as e:
        print(f"Error fetching holdings: {e}")
else:
    print("No access token found.")
