import sys
import os
sys.path.append(os.getcwd())
from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository

def list_trades():
    db = SessionLocal()
    repo = TradeRepository(db)
    trades = repo.get_all_open_trades()
    print(f"Found {len(trades)} open trades:")
    for t in trades:
        print(f" - {t.symbol} ({t.product}): Qty={t.qty}, Price={t.avg_price}, is_mtf={t.is_mtf}")
    db.close()

if __name__ == "__main__":
    list_trades()
