from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.all_models import OpenTrade
from app.core.config import get_settings
from datetime import datetime
import random

settings = get_settings()
engine = create_engine(settings.SUPABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def add_stocks():
    stocks = [
        ("RELIANCE", 2500.0),
        ("TCS", 3500.0),
        ("INFY", 1500.0),
        ("HDFCBANK", 1600.0),
        ("ICICIBANK", 950.0),
        ("SBIN", 600.0),
        ("BHARTIARTL", 900.0),
        ("ITC", 450.0),
        ("KOTAKBANK", 1800.0),
        ("LT", 3000.0)
    ]

    print("Adding sample stock trades...")
    for symbol, price in stocks:
        is_long = random.choice([True, False])
        qty = random.randint(1, 50)
        
        # Randomize price slightly
        price = price + random.uniform(-10, 10)
        
        trade = OpenTrade(
            symbol=symbol,
            instrument_token=0,
            qty=qty,
            avg_price=price,
            entry_date=datetime.now(),
            type="LONG" if is_long else "SHORT",
            exchange="NSE",
            max_exposure=int(qty * price),
            product="CNC" if is_long else "MIS",
            strategy_type="TRENDING",
            is_basket=0
        )
        db.add(trade)
    
    db.commit()
    print("Added 10 stock trades.")

if __name__ == "__main__":
    add_stocks()
