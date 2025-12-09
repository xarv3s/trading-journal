import sys
import os
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, TradeConstituent

def inspect_baskets():
    db = SessionLocal()
    baskets = db.query(OpenTrade).filter(OpenTrade.is_basket == 1).all()
    
    print(f"Found {len(baskets)} baskets:")
    for b in baskets:
        print(f"Basket ID: {b.id}, Symbol: {b.symbol}, Created: {b.entry_date}")
        constituents = db.query(TradeConstituent).filter(TradeConstituent.open_trade_id == b.id).all()
        print(f"  Constituents ({len(constituents)}):")
        for c in constituents:
            print(f"    - {c.symbol} ({c.type}) ID: {c.id}")
            
    db.close()

if __name__ == "__main__":
    inspect_baskets()
