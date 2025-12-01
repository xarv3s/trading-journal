import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Orderbook, OpenTrade, ClosedTrade
from repositories.trade_repository import TradeRepository
from services.kite_service import KiteClient
from datetime import datetime, timedelta

def test_3table_sync():
    print("\n--- Testing 3-Table Sync Logic ---")
    
    # 1. Setup DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    repo = TradeRepository(db)
    kite = KiteClient(api_key="test")
    
    # 2. Scenario 1: New Long Position
    print("\n[Scenario 1] New Long Position (Buy 10 @ 100)")
    orders_1 = [{
        'order_id': '1001',
        'status': 'COMPLETE',
        'order_timestamp': datetime.now(),
        'transaction_type': 'BUY',
        'tradingsymbol': 'INFY',
        'instrument_token': 123,
        'product': 'CNC',
        'quantity': 10,
        'average_price': 100.0,
        'exchange': 'NSE',
        'filled_quantity': 10,
        'pending_quantity': 0,
        'cancelled_quantity': 0
    }]
    df_1 = pd.DataFrame(orders_1)
    
    # Sync
    repo.save_orders(df_1)
    open_trades = repo.get_all_open_trades()
    ops = kite.process_trades(df_1, db_open_trades=open_trades)
    repo.apply_trade_operations(ops)
    
    # Verify
    ot = db.query(OpenTrade).filter(OpenTrade.symbol == 'INFY').first()
    assert ot is not None
    assert ot.qty == 10
    assert ot.avg_price == 100.0
    assert ot.type == 'LONG'
    print("Scenario 1 Passed!")
    
    # 3. Scenario 2: Accumulation (Buy 10 @ 110)
    print("\n[Scenario 2] Accumulation (Buy 10 @ 110)")
    orders_2 = [{
        'order_id': '1002',
        'status': 'COMPLETE',
        'order_timestamp': datetime.now() + timedelta(minutes=5),
        'transaction_type': 'BUY',
        'tradingsymbol': 'INFY',
        'instrument_token': 123,
        'product': 'CNC',
        'quantity': 10,
        'average_price': 110.0,
        'exchange': 'NSE',
        'filled_quantity': 10,
        'pending_quantity': 0,
        'cancelled_quantity': 0
    }]
    df_2 = pd.DataFrame(orders_2)
    
    # Sync
    repo.save_orders(df_2)
    open_trades = repo.get_all_open_trades()
    ops = kite.process_trades(df_2, db_open_trades=open_trades)
    repo.apply_trade_operations(ops)
    
    # Verify
    ot = db.query(OpenTrade).filter(OpenTrade.symbol == 'INFY').first()
    assert ot.qty == 20
    assert ot.avg_price == 105.0 # (1000 + 1100) / 20
    print("Scenario 2 Passed!")
    
    # 4. Scenario 3: Partial Exit (Sell 10 @ 120)
    print("\n[Scenario 3] Partial Exit (Sell 10 @ 120)")
    orders_3 = [{
        'order_id': '1003',
        'status': 'COMPLETE',
        'order_timestamp': datetime.now() + timedelta(minutes=10),
        'transaction_type': 'SELL',
        'tradingsymbol': 'INFY',
        'instrument_token': 123,
        'product': 'CNC',
        'quantity': 10,
        'average_price': 120.0,
        'exchange': 'NSE',
        'filled_quantity': 10,
        'pending_quantity': 0,
        'cancelled_quantity': 0
    }]
    df_3 = pd.DataFrame(orders_3)
    
    # Sync
    repo.save_orders(df_3)
    open_trades = repo.get_all_open_trades()
    ops = kite.process_trades(df_3, db_open_trades=open_trades)
    repo.apply_trade_operations(ops)
    
    # Verify Open Trade
    ot = db.query(OpenTrade).filter(OpenTrade.symbol == 'INFY').first()
    assert ot.qty == 10
    assert ot.avg_price == 105.0 # Avg price shouldn't change on reduction
    
    # Verify Closed Trade
    ct = db.query(ClosedTrade).filter(ClosedTrade.symbol == 'INFY').first()
    assert ct is not None
    assert ct.qty == 10
    assert ct.entry_price == 105.0
    assert ct.exit_price == 120.0
    assert ct.pnl == (120 - 105) * 10 # 150
    assert ct.closure_type == 'PARTIAL'
    print("Scenario 3 Passed!")
    
    # 5. Scenario 4: Full Exit (Sell 10 @ 130)
    print("\n[Scenario 4] Full Exit (Sell 10 @ 130)")
    orders_4 = [{
        'order_id': '1004',
        'status': 'COMPLETE',
        'order_timestamp': datetime.now() + timedelta(minutes=15),
        'transaction_type': 'SELL',
        'tradingsymbol': 'INFY',
        'instrument_token': 123,
        'product': 'CNC',
        'quantity': 10,
        'average_price': 130.0,
        'exchange': 'NSE',
        'filled_quantity': 10,
        'pending_quantity': 0,
        'cancelled_quantity': 0
    }]
    df_4 = pd.DataFrame(orders_4)
    
    # Sync
    repo.save_orders(df_4)
    open_trades = repo.get_all_open_trades()
    ops = kite.process_trades(df_4, db_open_trades=open_trades)
    repo.apply_trade_operations(ops)
    
    # Verify Open Trade Gone
    ot = db.query(OpenTrade).filter(OpenTrade.symbol == 'INFY').first()
    assert ot is None
    
    # Verify Closed Trade
    # Should be 2 closed trades now
    cts = db.query(ClosedTrade).filter(ClosedTrade.symbol == 'INFY').all()
    assert len(cts) == 2
    ct_last = cts[-1]
    assert ct_last.qty == 20 # Max exposure reported? Or just exit qty?
    # Logic: 'qty': current_pos['max_exposure']
    # Max exposure was 20.
    assert ct_last.qty == 20 
    assert ct_last.exit_price == 130.0
    assert ct_last.closure_type == 'FULL'
    print("Scenario 4 Passed!")

if __name__ == "__main__":
    test_3table_sync()
