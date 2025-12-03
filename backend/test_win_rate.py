import sys
import os
import pandas as pd
from datetime import datetime

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

from app.services.analytics_service import AnalyticsService

class MockTrade:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_win_rate():
    # Scenario:
    # 1. Open Trade (Should be ignored)
    # 2. Closed Trade (PARTIAL) - Profitable (Should be ignored)
    # 3. Closed Trade (FULL) - Profitable (Should be counted as Win)
    # 4. Closed Trade (FULL) - Loss (Should be counted as Loss)
    
    # Expected Win Rate = 1 Win / 2 Total Relevant = 50%
    
    trades = [
        MockTrade(
            id=1, status='OPEN', closure_type=None, pnl=0, net_pnl=0, 
            entry_date=datetime.now(), exit_date=datetime.now(), 
            entry_price=100, qty=10, is_mtf=0, segment='EQ'
        ),
        MockTrade(
            id=2, status='CLOSED', closure_type='PARTIAL', pnl=100, net_pnl=100, 
            entry_date=datetime.now(), exit_date=datetime.now(), 
            entry_price=100, exit_price=110, qty=10, is_mtf=0, segment='EQ'
        ),
        MockTrade(
            id=3, status='CLOSED', closure_type='FULL', pnl=200, net_pnl=200, 
            entry_date=datetime.now(), exit_date=datetime.now(), 
            entry_price=100, exit_price=120, qty=10, is_mtf=0, segment='EQ'
        ),
        MockTrade(
            id=4, status='CLOSED', closure_type='FULL', pnl=-50, net_pnl=-50, 
            entry_date=datetime.now(), exit_date=datetime.now(), 
            entry_price=100, exit_price=95, qty=10, is_mtf=0, segment='EQ'
        )
    ]
    
    # Note: AnalyticsService expects a list of objects or dicts. 
    # It also calculates net_pnl internally if not provided, but here I provided it.
    # Wait, AnalyticsService recalculates net_pnl in __init__.
    # So I should ensure pnl is set correctly.
    
    service = AnalyticsService(trades)
    
    # Force net_pnl to match pnl for simplicity (ignoring mtf_interest logic for this test)
    service.df['net_pnl'] = service.df['pnl'] 
    
    kpis = service.get_kpis()
    print(f"Win Rate: {kpis['win_rate']}%")
    
    if kpis['win_rate'] == 50.0:
        print("TEST PASSED")
    else:
        print(f"TEST FAILED. Expected 50.0, got {kpis['win_rate']}")

if __name__ == "__main__":
    test_win_rate()
