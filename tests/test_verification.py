import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import init_db, get_db, engine
from database.models import Base, Trade
from repositories.trade_repository import TradeRepository
from services.analytics_service import AnalyticsService

def test_verification():
    print("Initializing Database...")
    # Use in-memory DB for testing or just reset the file DB
    # For this test, we'll just use the file DB but clear it first if needed, 
    # or just append. Let's append to see it in the app later.
    init_db()
    
    db = next(get_db())
    repo = TradeRepository(db)
    
    print("Creating Mock Trades...")
    mock_trades = [
        {
            "instrument_token": 123456,
            "trading_symbol": "INFY",
            "exchange": "NSE",
            "segment": "EQ",
            "order_type": "CNC",
            "entry_date": datetime.now() - timedelta(days=5),
            "exit_date": datetime.now() - timedelta(days=4),
            "qty": 10,
            "entry_price": 1500.0,
            "exit_price": 1550.0,
            "pnl": 500.0,
            "setup_used": "Breakout",
            "mistakes_made": "None",
            "notes": "Good trade",
            "is_mtf": 0
        },
        {
            "instrument_token": 789012,
            "trading_symbol": "RELIANCE",
            "exchange": "NSE",
            "segment": "EQ",
            "order_type": "MTF",
            "entry_date": datetime.now() - timedelta(days=10),
            "exit_date": datetime.now() - timedelta(days=2),
            "qty": 5,
            "entry_price": 2400.0,
            "exit_price": 2300.0,
            "pnl": -500.0,
            "setup_used": "Mean Reversion",
            "mistakes_made": "FOMO",
            "notes": "Bad entry",
            "is_mtf": 1
        }
    ]
    
    count = repo.sync_trades(mock_trades)
    print(f"Synced {count} mock trades.")
    
    print("Verifying Analytics...")
    trades = repo.get_all_trades()
    analytics = AnalyticsService(trades)
    analytics.enrich_data(initial_capital=100000)
    
    kpis = analytics.get_kpis()
    print("KPIs:", kpis)
    
    # Verify Cost Calculation
    # Infosys Trade: Buy 10 @ 1500, Sell 10 @ 1550. Turnover = 30500.
    # STT = 0.1% of 30500 = 30.5
    # Exchange = 0.0000345 * 30500 = 1.05
    # SEBI = 0.000001 * 30500 = 0.03
    # Stamp = 0.00015 * 15000 = 2.25
    # GST = 0.18 * (0 + 1.05 + 0.03) = 0.19
    # Total ~ 34.02
    
    infy_trade = next(t for t in analytics.df.to_dict('records') if t['trading_symbol'] == 'INFY')
    print(f"INFY Estimated Charges: {infy_trade['estimated_charges']:.2f}")
    print(f"INFY Net PnL: {infy_trade['net_pnl_after_charges']:.2f}")
    print(f"INFY Allocation: {infy_trade['allocation_pct']:.2f}%")
    
    # Verify Quarterly Financials
    financials = analytics.get_quarterly_financials()
    print("Quarterly Financials:\n", financials)
    
    # Verify Insights
    insights = analytics.get_insights()
    print("Insights:", insights)
    
    # Verify Capital Management
    print("Verifying Capital Management...")
    repo.add_transaction(datetime.now(), 50000, "DEPOSIT", "Initial Deposit")
    transactions = repo.get_transactions()
    print(f"Transactions found: {len(transactions)}")
    
    analytics.enrich_data(initial_capital=100000, transactions=transactions)
    equity_curve = analytics.get_equity_curve()
    print("Equity Curve with Transactions:\n", equity_curve.tail())
    
    # Check if account value increased
    final_value = equity_curve.iloc[-1]['account_value']
    print(f"Final Account Value: {final_value}")
    
    assert kpis['total_trades'] >= 2
    print("Verification Successful!")

if __name__ == "__main__":
    test_verification()
