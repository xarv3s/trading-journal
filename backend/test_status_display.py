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

def test_status_display():
    mock_db = MockDB()
    repo = TradeRepository(mock_db)
    
    trades = repo.get_unified_trades()
    
    tatasteel = next(t for t in trades if t['trading_symbol'] == 'TATASTEEL')
    infy = next(t for t in trades if t['trading_symbol'] == 'INFY')
    
    print(f"TATASTEEL Status: {tatasteel['status']}")
    print(f"INFY Status: {infy['status']}")
    
    if tatasteel['status'] == 'PARTIAL' and infy['status'] == 'CLOSED':
        print("TEST PASSED")
    else:
        print("TEST FAILED")

if __name__ == "__main__":
    test_status_display()
