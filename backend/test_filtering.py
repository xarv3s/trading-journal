import sys
import os
from datetime import datetime

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

from app.repositories.trade_repository import TradeRepository
from app.models.all_models import ClosedTrade

class MockDB:
    def __init__(self):
        self.closed_trades = [
            ClosedTrade(
                id=1, symbol='TATASTEEL', closure_type='PARTIAL', 
                entry_date=datetime.now(), exit_date=datetime.now(),
                qty=5, entry_price=100, exit_price=110, pnl=50,
                type='LONG', exchange='NSE', product='CNC',
                strategy_type='TRENDING', is_mtf=0, is_basket=0
            ),
            ClosedTrade(
                id=2, symbol='INFY', closure_type='FULL', 
                entry_date=datetime.now(), exit_date=datetime.now(),
                qty=10, entry_price=1500, exit_price=1600, pnl=1000,
                type='LONG', exchange='NSE', product='CNC',
                strategy_type='TRENDING', is_mtf=0, is_basket=0
            )
        ]
        self.open_trades = []
        
    def query(self, model):
        class MockQuery:
            def __init__(self, data):
                self.data = data
            def all(self):
                return self.data
        
        if model.__name__ == 'ClosedTrade':
            return MockQuery(self.closed_trades)
        elif model.__name__ == 'OpenTrade':
            return MockQuery(self.open_trades)
        return MockQuery([])

def test_filtering():
    mock_db = MockDB()
    repo = TradeRepository(mock_db)
    
    # Test 1: Request CLOSED trades
    result = repo.get_paginated_trades(status='CLOSED')
    trades = result['data']
    
    print(f"Found {len(trades)} trades when status='CLOSED'")
    for t in trades:
        print(f" - {t['trading_symbol']} ({t['status']})")
        
    has_partial = any(t['status'] == 'PARTIAL' for t in trades)
    has_closed = any(t['status'] == 'CLOSED' for t in trades)
    
    if has_partial and has_closed:
        print("TEST PASSED")
    else:
        print("TEST FAILED")

if __name__ == "__main__":
    test_filtering()
