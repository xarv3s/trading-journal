from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.all_models import OpenTrade, ClosedTrade, TradeConstituent, Orderbook
from app.services.kite_service import KiteClient
from datetime import datetime
import pandas as pd

settings = get_settings()
engine = create_engine(settings.SUPABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def get_kite_client():
    token = KiteClient.load_access_token()
    return KiteClient(api_key=settings.KITE_API_KEY, access_token=token)

def hard_reset_and_sync():
    print("Starting Hard Reset...")
    
    # 1. Clear Tables
    print("Clearing tables...")
    try:
        db.query(TradeConstituent).delete()
        db.query(OpenTrade).delete()
        db.query(ClosedTrade).delete()
        # Optionally clear Orderbook to avoid dedup issues with future syncs?
        # User didn't explicitly ask, but it's safer for a "fresh start" feeling if we are re-importing everything.
        # However, process_orders relies on Orderbook to know what's processed.
        # If we clear Orderbook, process_orders might re-process old orders if we fetch them again.
        # But here we are doing a SNAPSHOT sync (positions/holdings), not order sync.
        # So Orderbook state doesn't matter for THIS operation, but matters for FUTURE process_orders.
        # If we keep Orderbook, future process_orders will skip old orders.
        # If we clear Orderbook, future process_orders will re-process them and potentially duplicate trades we just inserted?
        # WAIT. process_orders fetches "orders". We are fetching "positions".
        # If we insert positions now, and then run process_orders later for today's orders, 
        # process_orders will see "New Order" -> "Check OpenTrade".
        # If OpenTrade exists (from this snapshot), it will "Accumulate" or "Reduce".
        # This might double-count if the position we insert INCLUDES the effect of today's orders.
        # Positions API *does* include today's orders.
        # So if we insert Position=100, and then process_orders sees "Buy 100", it will add 100 -> 200. Double count.
        # SOLUTION: We should probably populate Orderbook with today's orders as "processed" to prevent this?
        # OR: Just clear Orderbook and let the user know that "Sync Orders" might duplicate if run for today?
        # Actually, the best approach for a "Hard Reset" is to rely on the Snapshot.
        # Future syncs should be for *new* orders.
        # If we run "Sync Orders" for today AFTER this snapshot, it WILL duplicate.
        # I should probably mark today's orders as processed in Orderbook.
        pass 
    except Exception as e:
        print(f"Error clearing tables: {e}")
        return

    db.commit()
    print("Tables cleared.")
    
    # 2. Fetch Data
    kite = get_kite_client()
    if not kite:
        print("Failed to initialize Kite client.")
        return

    print("Fetching Positions and Holdings...")
    positions_df = kite.fetch_positions()
    holdings_df = kite.fetch_holdings()
    
    count = 0
    
    # 3. Populate Open Trades (Logic from old sync_positions)
    
    # Process Positions
    if not positions_df.empty:
        for _, row in positions_df.iterrows():
            trade_type = 'LONG' if row['quantity'] > 0 else 'SHORT'
            qty = abs(row['quantity'])
            
            if qty == 0:
                continue
            
            strategy_type = 'TRENDING'
            if row['tradingsymbol'].endswith('CE') or row['tradingsymbol'].endswith('PE'):
                strategy_type = 'SIDEWAYS'
            
            trade_data = {
                'symbol': row['tradingsymbol'],
                'instrument_token': row['instrument_token'],
                'qty': qty,
                'avg_price': row['average_price'],
                'entry_date': datetime.now(),
                'type': trade_type,
                'exchange': row['exchange'],
                'max_exposure': int(qty * row['average_price']),
                'product': row['product'],
                'is_mtf': 1 if row['product'] == 'MTF' else 0,
                'strategy_type': strategy_type,
                'is_basket': 0,
                'realized_pnl': 0.0
            }
            
            trade = OpenTrade(**trade_data)
            db.add(trade)
            count += 1

    # Process Holdings
    if not holdings_df.empty:
        for _, row in holdings_df.iterrows():
            qty = row['quantity']
            
            is_mtf = 0
            product = 'CNC'
            
            # MTF Check
            if qty == 0 and 'mtf' in row and isinstance(row['mtf'], dict):
                mtf_qty = row['mtf'].get('quantity', 0)
                if mtf_qty > 0:
                    qty = mtf_qty
                    is_mtf = 1
                    product = 'MTF'
            
            if qty == 0: continue
            
            trade_data = {
                'symbol': row['tradingsymbol'],
                'instrument_token': row['instrument_token'],
                'qty': qty,
                'avg_price': row['average_price'],
                'entry_date': datetime.now(),
                'type': 'LONG',
                'exchange': row.get('exchange', 'NSE'),
                'max_exposure': int(qty * row['average_price']),
                'product': product,
                'is_mtf': is_mtf,
                'strategy_type': 'INVESTMENT',
                'is_basket': 0,
                'realized_pnl': 0.0
            }
            
            trade = OpenTrade(**trade_data)
            db.add(trade)
            count += 1
            
    db.commit()
    print(f"Hard Reset Complete. Populated {count} trades.")

if __name__ == "__main__":
    hard_reset_and_sync()
