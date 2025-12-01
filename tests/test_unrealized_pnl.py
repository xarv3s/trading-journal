import pandas as pd
from services.analytics_service import AnalyticsService
from datetime import datetime, timedelta

def test_unrealized_pnl():
    print("\n--- Testing Unrealized PnL in Equity Curve ---")
    
    # Mock Trades (Unified format)
    trades = [
        # Closed Trade
        {
            'id': 'CLOSED_1', 'entry_date': datetime(2023, 10, 1), 'exit_date': datetime(2023, 10, 5),
            'pnl': 1000, 'qty': 10, 'entry_price': 100, 'exit_price': 200, 'segment': 'EQ', 'is_mtf': 0, 'type': 'LONG', 'status': 'CLOSED'
        },
        # Open Trade (Simulating app.py update)
        {
            'id': 'OPEN_1', 'entry_date': datetime(2023, 11, 1), 
            # These fields would be set by app.py
            'exit_date': datetime.now(), 
            'exit_price': 150, # Current LTP
            'pnl': 500, # (150 - 100) * 10
            'qty': 10, 'entry_price': 100, 'segment': 'EQ', 'is_mtf': 0, 'type': 'LONG', 'status': 'OPEN_Unrealized'
        }
    ]
    
    analytics = AnalyticsService(trades)
    analytics.enrich_data(initial_capital=100000)
    
    # Check Equity Curve
    curve = analytics.get_equity_curve()
    print(curve)
    
    # Verify we have 2 points (or more depending on initial capital date handling)
    # Actually get_equity_curve returns points for each trade exit.
    assert len(curve) >= 2
    
    # Last point should reflect the open trade's PnL
    last_val = curve.iloc[-1]['account_value']
    # Initial 100000 + 1000 (Closed) + 500 (Open) - Charges
    # Charges for EQ: ~0.1% STT + others.
    # 1000 PnL -> Charges ~ (2000+1000)*0.001 = 3 + others.
    # 500 PnL -> Charges ~ (1500+1000)*0.001 = 2.5 + others.
    # Total PnL ~ 1500. Net ~ 1490+.
    
    assert last_val > 101400 
    assert last_val < 101500
    
    print("Unrealized PnL Test Passed!")

if __name__ == "__main__":
    test_unrealized_pnl()
