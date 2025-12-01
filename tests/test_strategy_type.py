import pandas as pd
from services.analytics_service import AnalyticsService
from database.models import OpenTrade
from datetime import datetime

def test_strategy_type_logic():
    print("\n--- Testing Strategy Type Logic ---")
    
    # 1. Test Analytics Filtering
    trades = [
        {'id': 1, 'pnl': 100, 'strategy_type': 'TRENDING', 'entry_date': datetime.now(), 'exit_date': datetime.now(), 'qty': 1, 'entry_price': 100, 'exit_price': 200, 'segment': 'EQ', 'is_mtf': 0},
        {'id': 2, 'pnl': -50, 'strategy_type': 'SIDEWAYS', 'entry_date': datetime.now(), 'exit_date': datetime.now(), 'qty': 1, 'entry_price': 100, 'exit_price': 50, 'segment': 'OPT', 'is_mtf': 0},
        {'id': 3, 'pnl': 200, 'strategy_type': 'TRENDING', 'entry_date': datetime.now(), 'exit_date': datetime.now(), 'qty': 1, 'entry_price': 100, 'exit_price': 300, 'segment': 'FUT', 'is_mtf': 0}
    ]
    
    analytics = AnalyticsService(trades)
    analytics.enrich_data()
    
    # Overall
    kpis_all = analytics.get_kpis()
    assert kpis_all['total_pnl'] > 200 # 100 - 50 + 200 = 250 (approx, minus charges)
    
    # Trending
    kpis_trend = analytics.get_kpis(strategy_type='TRENDING')
    # 100 + 200 = 300 Gross. Net ~ 290+.
    assert kpis_trend['total_trades'] == 2
    assert kpis_trend['total_pnl'] > 0
    
    # Sideways
    kpis_side = analytics.get_kpis(strategy_type='SIDEWAYS')
    # -50 Gross.
    assert kpis_side['total_trades'] == 1
    assert kpis_side['total_pnl'] < 0
    
    print("Analytics Filtering Passed!")
    
    # 2. Test Default Assignment Logic (Mocking KiteService logic)
    def get_strategy_type(symbol):
        if symbol.endswith('CE') or symbol.endswith('PE'):
            return 'SIDEWAYS'
        return 'TRENDING'
        
    assert get_strategy_type('INFY') == 'TRENDING'
    assert get_strategy_type('NIFTY23OCT19000CE') == 'SIDEWAYS'
    
    print("Default Assignment Logic Passed!")

if __name__ == "__main__":
    test_strategy_type_logic()
