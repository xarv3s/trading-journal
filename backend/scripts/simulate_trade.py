import sys
import os
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade

def simulate_trade():
    db = SessionLocal()
    try:
        # Symbol: NIFTY25DEC26000PE
        # Token: 18279170
        # Exchange: NFO
        
        trade = OpenTrade(
            symbol="NIFTY25DEC26000PE",
            instrument_token=18279170,
            qty=75, # 1 lot
            avg_price=120.0, # Arbitrary price
            entry_date=datetime.now(),
            type='LONG',
            exchange='NFO',
            product='NRML',
            strategy_type='SIMULATION',
            is_basket=0
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        print(f"Simulated trade created successfully: ID={trade.id}, Symbol={trade.symbol}")
        
    except Exception as e:
        print(f"Error creating simulated trade: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    simulate_trade()
