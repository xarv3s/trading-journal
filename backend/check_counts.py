from app.core.database import SessionLocal
from app.models.all_models import OpenTrade, ClosedTrade, Orderbook, TradeConstituent
from sqlalchemy import func

db = SessionLocal()

def count_rows(model):
    return db.query(func.count(model.id)).scalar() if hasattr(model, 'id') else db.query(func.count(model.order_id)).scalar()

print(f"Open Trades: {count_rows(OpenTrade)}")
print(f"Closed Trades: {count_rows(ClosedTrade)}")
print(f"Orderbook: {count_rows(Orderbook)}")
print(f"Constituents: {count_rows(TradeConstituent)}")

db.close()
