import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000/api/v1"

def create_dummy_trade(symbol, qty, price, type="LONG"):
    # This is a helper, but we don't have an endpoint to create open trades directly easily 
    # without going through the sync process or direct DB access.
    # However, for this test, I'll assume we can use the sync endpoint with mocked data OR
    # just insert into DB directly if I had DB access here. 
    # Since I don't have easy DB access from this script (it runs outside the app context),
    # I will try to use the `sync` endpoint if I can mock the kite client, which is hard.
    
    # Alternative: Use the `trade_repository` directly in a script that imports the app.
    pass

# Since I cannot easily hit the API to create dummy trades (as they come from Kite sync),
# I will write a script that imports the app code and runs the test using the repository directly.
# This is better as it tests the logic without needing the full server running or Kite connection.

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository
from app.models.all_models import OpenTrade

def test_basket_creation():
    db = SessionLocal()
    repo = TradeRepository(db)
    
    # 1. Create 2 dummy open trades
    t1 = OpenTrade(
        symbol="TEST_T1", instrument_token=1, qty=10, avg_price=100, 
        entry_date=datetime.now(), type="LONG", exchange="NSE", 
        max_exposure=1000, product="MIS", strategy_type="TRENDING"
    )
    t2 = OpenTrade(
        symbol="TEST_T2", instrument_token=2, qty=20, avg_price=50, 
        entry_date=datetime.now(), type="SHORT", exchange="NSE", 
        max_exposure=1000, product="MIS", strategy_type="TRENDING"
    )
    
    db.add(t1)
    db.add(t2)
    db.commit()
    db.refresh(t1)
    db.refresh(t2)
    
    print(f"Created trades: {t1.id}, {t2.id}")
    
    # 2. Create Basket
    basket = repo.create_basket("TEST_BASKET", [t1.id, t2.id], "IRON_CONDOR")
    
    if basket:
        print(f"Basket created: {basket.id}, Symbol: {basket.symbol}")
        print(f"Is Basket: {basket.is_basket}")
        
        # 3. Verify constituents
        constituents = repo.get_basket_constituents(open_trade_id=basket.id)
        print(f"Constituents count: {len(constituents)}")
        for c in constituents:
            print(f" - {c.symbol} ({c.type})")
            
        # 4. Verify original trades are gone
        old_t1 = db.query(OpenTrade).filter(OpenTrade.id == t1.id).first()
        old_t2 = db.query(OpenTrade).filter(OpenTrade.id == t2.id).first()
        
        if not old_t1 and not old_t2:
            print("Original trades deleted successfully.")
        else:
            print("Error: Original trades still exist!")
            
        # Cleanup
        db.delete(basket) # Should cascade? No, need to delete constituents manually or rely on cascade if configured
        # For now just manual cleanup
        for c in constituents:
            db.delete(c)
        db.commit()
        print("Cleanup done.")
        
    else:
        print("Failed to create basket.")
        
    db.close()

if __name__ == "__main__":
    test_basket_creation()
