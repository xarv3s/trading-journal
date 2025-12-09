from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.all_models import OpenTrade, TradeConstituent, Base
from app.core.config import get_settings
from datetime import datetime

settings = get_settings()
engine = create_engine(settings.SUPABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def setup_data():
    # Clear existing open trades and constituents
    print("Clearing existing open trades and constituents...")
    db.query(TradeConstituent).delete()
    db.query(OpenTrade).delete()
    db.commit()

    # Define Iron Condor Legs (Dec 2025)
    # Assuming Spot is around 24500 for the sake of example strikes
    trades = [
        # OTM Put Wing (Long Hedge)
        {
            "symbol": "NIFTY25DEC23500PE",
            "trading_symbol": "NIFTY25DEC23500PE",
            "exchange": "NFO",
            "type": "LONG",
            "qty": 50,
            "avg_price": 150.0,
            "product": "NRML",
            "strategy_type": "SIDEWAYS"
        },
        # OTM Put Sell
        {
            "symbol": "NIFTY25DEC24000PE",
            "trading_symbol": "NIFTY25DEC24000PE",
            "exchange": "NFO",
            "type": "SHORT",
            "qty": 50,
            "avg_price": 300.0,
            "product": "NRML",
            "strategy_type": "SIDEWAYS"
        },
        # OTM Call Sell
        {
            "symbol": "NIFTY25DEC25000CE",
            "trading_symbol": "NIFTY25DEC25000CE",
            "exchange": "NFO",
            "type": "SHORT",
            "qty": 50,
            "avg_price": 320.0,
            "product": "NRML",
            "strategy_type": "SIDEWAYS"
        },
        # OTM Call Wing (Long Hedge)
        {
            "symbol": "NIFTY25DEC25500CE",
            "trading_symbol": "NIFTY25DEC25500CE",
            "exchange": "NFO",
            "type": "LONG",
            "qty": 50,
            "avg_price": 160.0,
            "product": "NRML",
            "strategy_type": "SIDEWAYS"
        }
    ]

    print("Inserting new trades...")
    for t in trades:
        trade = OpenTrade(
            symbol=t["symbol"],
            instrument_token=0, # Mock token
            qty=t["qty"],
            avg_price=t["avg_price"],
            entry_date=datetime.now(),
            type=t["type"],
            exchange=t["exchange"],
            max_exposure=int(t["qty"] * t["avg_price"]),
            product=t["product"],
            strategy_type=t["strategy_type"],
            is_basket=0
        )
        db.add(trade)
    
    db.commit()
    print("Done!")

if __name__ == "__main__":
    setup_data()
