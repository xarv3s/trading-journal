import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, OpenTrade, ClosedTrade
from repositories.trade_repository import TradeRepository
from datetime import datetime

def test_ui_logic():
    print("\n--- Testing UI Logic (Unified Trades & Updates) ---")
    
    # 1. Setup DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    repo = TradeRepository(db)
    
    # 2. Seed Data
    ot = OpenTrade(
        symbol='INFY', qty=10, avg_price=100.0, entry_date=datetime.now(), 
        type='LONG', exchange='NSE', max_exposure=10, product='CNC'
    )
    ct = ClosedTrade(
        symbol='TCS', qty=5, entry_price=2000.0, exit_price=2100.0, 
        entry_date=datetime.now(), exit_date=datetime.now(), pnl=500.0, 
        type='LONG', exchange='NSE', closure_type='FULL', product='CNC'
    )
    db.add(ot)
    db.add(ct)
    db.commit()
    db.refresh(ot)
    db.refresh(ct)
    
    # 3. Test get_unified_trades
    print("\n[Test] get_unified_trades")
    trades = repo.get_unified_trades()
    assert len(trades) == 2
    
    open_t = next(t for t in trades if t['status'] == 'OPEN')
    closed_t = next(t for t in trades if t['status'] == 'CLOSED')
    
    assert open_t['trading_symbol'] == 'INFY'
    assert open_t['id'] == f"OPEN_{ot.id}"
    assert open_t['source_table'] == 'OPEN'
    
    assert closed_t['trading_symbol'] == 'TCS'
    assert closed_t['id'] == f"CLOSED_{ct.id}"
    assert closed_t['source_table'] == 'CLOSED'
    print("get_unified_trades Passed!")
    
    # 4. Test update_trade (Open Trade)
    print("\n[Test] update_trade (Open Trade)")
    repo.update_trade(open_t['id'], {'notes': 'Holding for target', 'setup_used': 'Breakout'})
    
    db.refresh(ot)
    assert ot.notes == 'Holding for target'
    assert ot.setup_used == 'Breakout'
    print("update_trade (Open) Passed!")
    
    # 5. Test update_trade (Closed Trade)
    print("\n[Test] update_trade (Closed Trade)")
    repo.update_trade(closed_t['id'], {'mistakes_made': 'FOMO', 'is_mtf': 1})
    
    db.refresh(ct)
    assert ct.mistakes_made == 'FOMO'
    assert ct.is_mtf == 1
    print("update_trade (Closed) Passed!")

if __name__ == "__main__":
    test_ui_logic()
