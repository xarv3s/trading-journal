import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade

def add_iron_condor():
    db = SessionLocal()
    
    # Nifty Spot approx 24000 (hypothetical)
    # Iron Condor:
    # 1. Buy 23500 PE (Long Put Wing)
    # 2. Sell 23800 PE (Short Put Body)
    # 3. Sell 24200 CE (Short Call Body)
    # 4. Buy 24500 CE (Long Call Wing)
    
    trades = [
        {
            "symbol": "NIFTY24DEC23500PE",
            "instrument_token": 1001,
            "qty": 50,
            "avg_price": 20.0,
            "type": "LONG",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "IRON_CONDOR" 
        },
        {
            "symbol": "NIFTY24DEC23800PE",
            "instrument_token": 1002,
            "qty": 50,
            "avg_price": 80.0,
            "type": "SHORT",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "IRON_CONDOR"
        },
        {
            "symbol": "NIFTY24DEC24200CE",
            "instrument_token": 1003,
            "qty": 50,
            "avg_price": 90.0,
            "type": "SHORT",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "IRON_CONDOR"
        },
        {
            "symbol": "NIFTY24DEC24500CE",
            "instrument_token": 1004,
            "qty": 50,
            "avg_price": 25.0,
            "type": "LONG",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "IRON_CONDOR"
        }
    ]
    
    for t in trades:
        # Check if exists to avoid duplicates
        existing = db.query(OpenTrade).filter(OpenTrade.symbol == t["symbol"]).first()
        if existing:
            print(f"Trade for {t['symbol']} already exists, skipping.")
            continue
            
        trade = OpenTrade(
            symbol=t["symbol"],
            instrument_token=t["instrument_token"],
            qty=t["qty"],
            avg_price=t["avg_price"],
            entry_date=datetime.now(),
            type=t["type"],
            exchange=t["exchange"],
            max_exposure=t["qty"],
            product=t["product"],
            strategy_type=t["strategy_type"],
            is_basket=0
        )
        db.add(trade)
        print(f"Added {t['symbol']}")
    
    db.commit()
    print("Finished adding trades.")
    db.close()

if __name__ == "__main__":
    add_iron_condor()
