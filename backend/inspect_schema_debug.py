import sys
import os
from sqlalchemy import inspect
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.database import engine
from app.models.all_models import TradeConstituent

def inspect_schema():
    inspector = inspect(engine)
    columns = inspector.get_columns('trade_constituents')
    for c in columns:
        print(f"Column: {c['name']}, Type: {c['type']}")

if __name__ == "__main__":
    inspect_schema()
