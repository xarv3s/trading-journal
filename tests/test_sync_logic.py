import pandas as pd
from services.kite_service import KiteClient
from database.models import Trade
from datetime import datetime, timedelta

def test_accumulation():
    print("\n--- Testing Accumulation ---")
    kite = KiteClient(api_key="test")
    
    # Existing Open Trade: 10 Qty @ 100
    open_trade = Trade(
        id=1,
        instrument_token=123,
        trading_symbol="INFY",
        exchange="NSE",
        order_type="CNC",
        entry_date=datetime.now(),
        qty=10,
        entry_price=100.0,
        exit_date=None
    )
    
    # New Order: Buy 10 @ 110
    orders_data = [{
        'instrument_token': 123,
        'tradingsymbol': 'INFY',
        'exchange': 'NSE',
        'transaction_type': 'BUY',
        'quantity': 10,
        'average_price': 110.0,
        'order_timestamp': (datetime.now() + timedelta(minutes=5)).isoformat(),
        'status': 'COMPLETE',
        'product': 'CNC'
    }]
    orders_df = pd.DataFrame(orders_data)
    
    results = kite.process_trades(orders_df, db_open_trades=[open_trade])
    
    print(f"Results count: {len(results)}")
    if len(results) == 1:
        trade = results[0]
        print(f"Trade ID: {trade.get('id')}")
        print(f"New Qty: {trade['qty']}")
        print(f"New Avg Price: {trade['entry_price']}")
        
        assert trade['id'] == 1
        assert trade['qty'] == 20
        assert trade['entry_price'] == 105.0
        print("Accumulation Passed!")
    else:
        print("Accumulation Failed: Expected 1 updated trade.")

def test_partial_exit():
    print("\n--- Testing Partial Exit ---")
    kite = KiteClient(api_key="test")
    
    # Existing Open Trade: 20 Qty @ 105
    open_trade = Trade(
        id=1,
        instrument_token=123,
        trading_symbol="INFY",
        exchange="NSE",
        order_type="CNC",
        entry_date=datetime.now(),
        qty=20,
        entry_price=105.0,
        exit_date=None
    )
    
    # New Order: Sell 10 @ 115
    orders_data = [{
        'instrument_token': 123,
        'tradingsymbol': 'INFY',
        'exchange': 'NSE',
        'transaction_type': 'SELL',
        'quantity': 10,
        'average_price': 115.0,
        'order_timestamp': (datetime.now() + timedelta(minutes=10)).isoformat(),
        'status': 'COMPLETE',
        'product': 'CNC'
    }]
    orders_df = pd.DataFrame(orders_data)
    
    results = kite.process_trades(orders_df, db_open_trades=[open_trade])
    
    print(f"Results count: {len(results)}")
    # Expect: 1 Update (Open Trade reduced) + 1 New (Closed Trade)
    if len(results) == 2:
        # Check Update
        update = next(t for t in results if 'id' in t and t['id'] == 1)
        print(f"Updated Trade Qty: {update['qty']}")
        assert update['qty'] == 10
        
        # Check New Closed Trade
        closed = next(t for t in results if 'id' not in t or t['id'] is None)
        print(f"Closed Trade Qty: {closed['qty']}")
        print(f"Closed Trade PnL: {closed['pnl']}")
        
        assert closed['qty'] == 10
        assert closed['pnl'] == (115 - 105) * 10 # 100
        assert closed['exit_date'] is not None
        print("Partial Exit Passed!")
    else:
        print("Partial Exit Failed: Expected 2 records.")

def test_full_exit():
    print("\n--- Testing Full Exit ---")
    kite = KiteClient(api_key="test")
    
    # Existing Open Trade: 10 Qty @ 105
    open_trade = Trade(
        id=1,
        instrument_token=123,
        trading_symbol="INFY",
        exchange="NSE",
        order_type="CNC",
        entry_date=datetime.now(),
        qty=10,
        entry_price=105.0,
        exit_date=None
    )
    
    # New Order: Sell 10 @ 115
    orders_data = [{
        'instrument_token': 123,
        'tradingsymbol': 'INFY',
        'exchange': 'NSE',
        'transaction_type': 'SELL',
        'quantity': 10,
        'average_price': 115.0,
        'order_timestamp': (datetime.now() + timedelta(minutes=15)).isoformat(),
        'status': 'COMPLETE',
        'product': 'CNC'
    }]
    orders_df = pd.DataFrame(orders_data)
    
    results = kite.process_trades(orders_df, db_open_trades=[open_trade])
    
    print(f"Results count: {len(results)}")
    if len(results) == 1:
        trade = results[0]
        print(f"Trade ID: {trade.get('id')}")
        print(f"Exit Price: {trade['exit_price']}")
        print(f"PnL: {trade['pnl']}")
        
        assert trade['id'] == 1
        assert trade['exit_date'] is not None
        assert trade['pnl'] == 100.0
        print("Full Exit Passed!")
    else:
        print("Full Exit Failed: Expected 1 updated trade.")

if __name__ == "__main__":
    test_accumulation()
    test_partial_exit()
    test_full_exit()
