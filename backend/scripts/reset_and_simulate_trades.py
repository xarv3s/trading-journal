import sys
import os
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, TradeConstituent

def reset_and_simulate():
    db = SessionLocal()
    try:
        print("Clearing existing baskets and simulated trades...")
        # 1. Delete all TradeConstituents
        db.query(TradeConstituent).delete()
        
        # 2. Delete all Baskets
        db.query(OpenTrade).filter(OpenTrade.is_basket == 1).delete()
        
        # 3. Delete previous simulated trades
        db.query(OpenTrade).filter(OpenTrade.strategy_type == 'SIMULATION').delete()
        
        db.commit()
        print("Cleanup complete.")
        
        # 4. Create 4 new simulated trades
        trades_data = [
            # NIFTY25DEC26000CE
            {
                "symbol": "NIFTY25DEC26000CE",
                "instrument_token": 18278146,
                "qty": 75,
                "avg_price": 150.0,
                "type": "LONG"
            },
            # NIFTY25DEC26000PE
            {
                "symbol": "NIFTY25DEC26000PE",
                "instrument_token": 18279170,
                "qty": 75,
                "avg_price": 120.0,
                "type": "LONG"
            },
            # NIFTY25DEC26500CE
            {
                "symbol": "NIFTY25DEC26500CE",
                "instrument_token": 16817922,
                "qty": 75,
                "avg_price": 80.0,
                "type": "LONG"
            },
            # NIFTY25DEC26500PE
            {
                "symbol": "NIFTY25DEC26500PE",
                "instrument_token": 16819458,
                "qty": 75,
                "avg_price": 200.0,
                "type": "LONG"
            }
        ]
        
        print("Creating 4 new simulated trades...")
        for t_data in trades_data:
            trade = OpenTrade(
                symbol=t_data["symbol"],
                instrument_token=t_data["instrument_token"],
                qty=t_data["qty"],
                avg_price=t_data["avg_price"],
                entry_date=datetime.now(),
                type=t_data["type"],
                exchange='NFO',
                product='NRML',
                strategy_type='SIMULATION',
                is_basket=0
            )
            db.add(trade)
            
        db.commit()
        print("Successfully created 4 simulated trades.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_simulate()
