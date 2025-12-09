import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade

def simulate_user_trades():
    db = SessionLocal()
    
    print("Simulating user requested trades (Corrected)...")
    
    # User Request:
    # Lot Size: 75
    # Execution Date: December 2, 2025
    
    # Trades:
    # 1. Sell NIFTY 9th w DEC 25700 PE: 26.00
    # 2. Sell NIFTY 9th w DEC 26250CE: 78.2
    # 3. Buy NIFTY 26DEC 28000 PE: 1168.00
    # 4. Buy NIFTY 26MAR 25000 CE: 1830
    # 5. Buy NIFTY 26MAR 25000 PE: 173.75
    
    # Symbol Logic:
    # - 9th w DEC (2025) -> NIFTY25D09... (Weekly)
    # - 26DEC (2026) -> NIFTY26DEC... (Monthly)
    # - 26MAR (2026) -> NIFTY26MAR... (Monthly)
    
    entry_date = datetime(2025, 12, 2, 9, 15, 0) # Dec 2, 2025, 9:15 AM
    lot_size = 75
    
    trades_data = [
        {
            "symbol": "NIFTY25D0925700PE", 
            "instrument_token": 3001,
            "qty": lot_size,
            "avg_price": 26.00,
            "type": "SHORT",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "USER_SIM",
            "notes": "Exp: 9 Dec 2025 (Weekly)"
        },
        {
            "symbol": "NIFTY25D0926250CE", 
            "instrument_token": 3002,
            "qty": lot_size,
            "avg_price": 78.20,
            "type": "SHORT",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "USER_SIM",
            "notes": "Exp: 9 Dec 2025 (Weekly)"
        },
        {
            "symbol": "NIFTY26DEC28000PE", 
            "instrument_token": 3003,
            "qty": lot_size,
            "avg_price": 1168.00,
            "type": "LONG",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "USER_SIM",
            "notes": "Exp: Dec 2026 (Monthly)"
        },
        {
            "symbol": "NIFTY26MAR25000CE", 
            "instrument_token": 3004,
            "qty": lot_size,
            "avg_price": 1830.00,
            "type": "LONG",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "USER_SIM",
            "notes": "Exp: Mar 2026 (Monthly)"
        },
        {
            "symbol": "NIFTY26MAR25000PE", 
            "instrument_token": 3005,
            "qty": lot_size,
            "avg_price": 173.75,
            "type": "LONG",
            "exchange": "NFO",
            "product": "NRML",
            "strategy_type": "USER_SIM",
            "notes": "Exp: Mar 2026 (Monthly)"
        }
    ]
    
    for t in trades_data:
        # Check if exists
        existing = db.query(OpenTrade).filter(OpenTrade.symbol == t["symbol"]).first()
        if existing:
            print(f"Trade for {t['symbol']} already exists, skipping.")
            continue
            
        trade = OpenTrade(
            symbol=t["symbol"],
            instrument_token=t["instrument_token"],
            qty=t["qty"],
            avg_price=t["avg_price"],
            entry_date=entry_date,
            type=t["type"],
            exchange=t["exchange"],
            max_exposure=t["qty"] * t["avg_price"],
            product=t["product"],
            strategy_type=t["strategy_type"],
            notes=t["notes"],
            is_basket=0
        )
        db.add(trade)
        print(f"Added {t['type']} {t['symbol']} @ {t['avg_price']}")
    
    db.commit()
    print("Finished adding user simulated trades.")
    db.close()

if __name__ == "__main__":
    simulate_user_trades()
