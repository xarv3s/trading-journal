import pandas as pd
from services.analytics_service import AnalyticsService
from datetime import datetime, timedelta

def test_monthly_stats():
    print("\n--- Testing get_monthly_stats ---")
    
    # Mock Data
    trades = [
        {
            'id': 1, 'entry_date': datetime(2023, 10, 1), 'exit_date': datetime(2023, 10, 5),
            'pnl': 1000, 'qty': 10, 'entry_price': 100, 'exit_price': 200, 'segment': 'EQ', 'is_mtf': 0
        },
        {
            'id': 2, 'entry_date': datetime(2023, 10, 10), 'exit_date': datetime(2023, 10, 15),
            'pnl': -500, 'qty': 10, 'entry_price': 200, 'exit_price': 150, 'segment': 'EQ', 'is_mtf': 0
        },
        {
            'id': 3, 'entry_date': datetime(2023, 11, 1), 'exit_date': datetime(2023, 11, 5),
            'pnl': 2000, 'qty': 10, 'entry_price': 100, 'exit_price': 300, 'segment': 'EQ', 'is_mtf': 0
        }
    ]
    
    analytics = AnalyticsService(trades)
    analytics.enrich_data()
    
    stats = analytics.get_monthly_stats()
    print(stats)
    
    # Verify Columns
    expected_cols = ['month_year', 'net_pnl', 'estimated_charges', 'trades_count']
    for col in expected_cols:
        assert col in stats.columns
        
    # Verify Aggregation
    # Oct 2023: +1000 - 500 = 500 Gross. Net will be slightly less due to charges.
    # Nov 2023: +2000 Gross.
    
    oct_row = stats[stats['month_year'] == '2023-10'].iloc[0]
    nov_row = stats[stats['month_year'] == '2023-11'].iloc[0]
    
    assert oct_row['trades_count'] == 2
    assert nov_row['trades_count'] == 1
    
    print("get_monthly_stats Passed!")

if __name__ == "__main__":
    test_monthly_stats()
