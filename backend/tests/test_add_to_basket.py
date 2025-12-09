import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository
from app.models.all_models import OpenTrade, TradeConstituent
from datetime import datetime

def test_add_to_basket():
    db_session = SessionLocal()
    try:
        repo = TradeRepository(db_session)
        
        # 1. Create Dummy Trades
        print("Creating dummy trades...")
        t1 = OpenTrade(
            symbol="T1", instrument_token=1, qty=100, avg_price=100, 
            entry_date=datetime.now(), type='LONG', exchange='NSE', 
            product='NRML', strategy_type='TEST'
        )
        t2 = OpenTrade(
            symbol="T2", instrument_token=2, qty=50, avg_price=200, 
            entry_date=datetime.now(), type='LONG', exchange='NSE', 
            product='NRML', strategy_type='TEST'
        )
        db_session.add(t1)
        db_session.add(t2)
        db_session.commit()
        db_session.refresh(t1)
        db_session.refresh(t2)
        
        # 2. Create Basket with T1
        print("Creating basket...")
        basket = repo.create_basket("BASKET1", [t1.id], "TEST")
        if not basket:
            print("Failed to create basket")
            return
            
        print(f"Basket created: Qty={basket.qty}, Avg={basket.avg_price}")
        # If lot size is 1, lots = 100. Basket Qty = 100.
        
        # 3. Add T2 to Basket
        print("Adding trade to basket...")
        updated_basket = repo.add_to_basket(basket.id, [t2.id])
        if not updated_basket:
            print("Failed to add to basket")
            return
        
        # 4. Verify
        # Total Invested: (100*100) + (50*200) = 10000 + 10000 = 20000
        # Total Lots: 100 + 50 = 150
        # Total Constituents: 2
        # New Basket Qty: 150 / 2 = 75
        # New Avg Price: 20000 / 75 = 266.66
        
        print(f"Updated Basket: Qty={updated_basket.qty}, Avg={updated_basket.avg_price}")
        
        assert updated_basket.qty == 75, f"Expected Qty 75, got {updated_basket.qty}"
        assert abs(updated_basket.avg_price - 266.66) < 0.1, f"Expected Avg 266.66, got {updated_basket.avg_price}"
        
        constituents = repo.get_basket_constituents(open_trade_id=updated_basket.id)
        assert len(constituents) == 2, f"Expected 2 constituents, got {len(constituents)}"
        symbols = {c.symbol for c in constituents}
        assert "T1" in symbols
        assert "T2" in symbols
        
        print("Test Passed!")
        
        # Cleanup
        db_session.delete(updated_basket)
        for c in constituents:
            db_session.delete(c)
        db_session.commit()
        
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_session.close()

if __name__ == "__main__":
    test_add_to_basket()
