from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.all_models import Orderbook, TradeConstituent, OpenTrade
import pandas as pd

settings = get_settings()
engine = create_engine(settings.SUPABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- Recent Orders ---")
orders = db.query(Orderbook).order_by(Orderbook.order_timestamp.desc()).limit(5).all()
for o in orders:
    print(f"ID: {o.order_id}, Symbol: {o.tradingsymbol}, Type: {o.transaction_type}, Qty: {o.quantity}, Status: {o.status}")

print("\n--- Constituents ---")
constituents = db.query(TradeConstituent).all()
for c in constituents:
    print(f"ID: {c.id}, Symbol: {c.symbol}, Type: {c.type}, Qty: {c.qty}, BasketID: {c.open_trade_id}")
