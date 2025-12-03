import sys
import os
from datetime import datetime, timedelta
import pytz

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.services.kite_service import KiteClient
from app.core.config import get_settings

def check_status():
    settings = get_settings()
    # Load token
    token = KiteClient.load_access_token()
    if not token:
        print("No access token found.")
        return

    kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
    
    try:
        # Fetch quote for RELIANCE
        quote = kite.kite.quote("NSE:RELIANCE")
        if "NSE:RELIANCE" not in quote:
            print("Could not fetch quote.")
            return

        data = quote["NSE:RELIANCE"]
        print("Quote Data Keys:", data.keys())
        
        last_trade_time = data.get('last_trade_time')
        timestamp = data.get('timestamp')
        
        print(f"Last Trade Time: {last_trade_time}")
        print(f"Timestamp: {timestamp}")
        print(f"Current Time: {datetime.now(pytz.timezone('Asia/Kolkata'))}")
        
        if timestamp:
            # Check if timestamp is aware
            if timestamp.tzinfo is None:
                # Assume it is IST if naive (Kite usually returns IST)
                # Or just compare with naive local time
                now = datetime.now()
            else:
                now = datetime.now(pytz.timezone('Asia/Kolkata'))
                
            print(f"Timestamp (Type: {type(timestamp)}): {timestamp}")
            print(f"Now: {now}")
            
            diff = now - timestamp
            print(f"Difference: {diff}")
            
            if diff < timedelta(minutes=5):
                print("Market Status: OPEN")
            else:
                print("Market Status: CLOSED")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()
