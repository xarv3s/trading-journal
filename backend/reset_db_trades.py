from app.core.database import engine
from sqlalchemy import text

print("Resetting trade tables...")

with engine.connect() as conn:
    # Disable foreign key checks temporarily if needed, but truncation usually handles it if ordered correctly or with CASCADE
    conn.execute(text("TRUNCATE TABLE trade_constituents, open_trades, closed_trades, orderbook CASCADE"))
    conn.commit()

print("All trade data cleared. Ready for fresh sync.")
