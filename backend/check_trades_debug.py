from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository

db = SessionLocal()
repo = TradeRepository(db)
unified = repo.get_unified_trades()
print(f"Total unified trades: {len(unified)}")
closed = [t for t in unified if t['source_table'] == 'CLOSED']
print(f"Closed trades: {len(closed)}")
open_trades = [t for t in unified if t['source_table'] == 'OPEN']
print(f"Open trades: {len(open_trades)}")

for t in closed:
    print(f"Closed trade: {t['id']} Exit Date: {t['exit_date']}")
