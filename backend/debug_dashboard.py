import sys
from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository
from app.services.analytics_service import AnalyticsService

print("Starting Dashboard Debug...")

try:
    db = SessionLocal()
    repo = TradeRepository(db)
    
    print("Fetching unified trades...")
    unified_trades = repo.get_unified_trades()
    print(f"Fetched {len(unified_trades)} trades.")
    
    print("Initializing AnalyticsService...")
    analytics = AnalyticsService(unified_trades)
    
    print("Enriching data...")
    analytics.enrich_data()
    
    print("Calculating KPIs...")
    kpis = analytics.get_kpis()
    print(f"KPIs: {kpis}")
    
    print("Calculating Equity Curve...")
    equity_curve = analytics.get_equity_curve()
    print(f"Equity Curve rows: {len(equity_curve)}")
    
    print("Calculating PnL Distribution...")
    pnl_dist = analytics.get_pnl_distribution()
    print(f"PnL Distribution size: {len(pnl_dist)}")
    
    print("SUCCESS: Dashboard data generated without error.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
