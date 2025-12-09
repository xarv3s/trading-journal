import sys
import os
from datetime import datetime, timedelta
import random

# Add the current directory to sys.path to make app module importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade

def add_sample_diagonal_spread():
    db = SessionLocal()
    try:
        # Define the 4 legs of a Nifty Diagonal Calendar Spread
        # Dec 2025 (Near) and Jan 2026 (Far)
        # Assuming Nifty Spot ~ 24500
        
        entry_date = datetime.now()
        
        trades = [
            {
                "symbol": "NIFTY25DEC25000CE",
                "instrument_token": 100001,
                "qty": 75, # 1 Lot
                "avg_price": 150.0,
                "entry_date": entry_date,
                "type": "SHORT",
                "exchange": "NFO",
                "product": "NRML",
                "strategy_type": "DIAGONAL",
                "is_basket": 0,
                "max_exposure": 75
            },
            {
                "symbol": "NIFTY26JAN25500CE",
                "instrument_token": 100002,
                "qty": 75,
                "avg_price": 200.0,
                "entry_date": entry_date,
                "type": "LONG",
                "exchange": "NFO",
                "product": "NRML",
                "strategy_type": "DIAGONAL",
                "is_basket": 0,
                "max_exposure": 75
            },
            {
                "symbol": "NIFTY25DEC24000PE",
                "instrument_token": 100003,
                "qty": 75,
                "avg_price": 140.0,
                "entry_date": entry_date,
                "type": "SHORT",
                "exchange": "NFO",
                "product": "NRML",
                "strategy_type": "DIAGONAL",
                "is_basket": 0,
                "max_exposure": 75
            },
            {
                "symbol": "NIFTY26JAN23500PE",
                "instrument_token": 100004,
                "qty": 75,
                "avg_price": 180.0,
                "entry_date": entry_date,
                "type": "LONG",
                "exchange": "NFO",
                "product": "NRML",
                "strategy_type": "DIAGONAL",
                "is_basket": 0,
                "max_exposure": 75
            }
        ]
        
        print("Adding sample diagonal spread trades...")
        for t in trades:
            trade = OpenTrade(**t)
            db.add(trade)
            print(f"Added {t['symbol']} ({t['type']})")
            
        db.commit()
        print("Successfully added 4 legs.")
        
    except Exception as e:
        print(f"Error adding trades: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_diagonal_spread()
