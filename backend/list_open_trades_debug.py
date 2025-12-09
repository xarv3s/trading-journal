import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.all_models import OpenTrade

def list_trades():
    db = SessionLocal()
    trades = db.query(OpenTrade).all()
    for t in trades:
        print(f"ID: {t.id}, Symbol: {t.symbol}, Type: {t.type}, IsBasket: {t.is_basket}")
    db.close()

if __name__ == "__main__":
    list_trades()
