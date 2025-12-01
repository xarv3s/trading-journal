import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from credentials.env
load_dotenv("credentials.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    print("Error: SUPABASE_URL must be set in credentials.env file")
    print("Format: postgresql://user:password@host:port/dbname")
    exit(1)

# Create SQLAlchemy Engine
try:
    engine = create_engine(SUPABASE_URL)
    with engine.connect() as conn:
        print("Connected to Database successfully!")
except Exception as e:
    print(f"Error connecting to database: {e}")
    exit(1)

def upload_orderbook(eq_csv_path, fo_csv_path):
    print("Reading CSV files...")
    try:
        df_eq = pd.read_csv(eq_csv_path)
        df_fo = pd.read_csv(fo_csv_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None

    orders = []
    
    for df in [df_eq, df_fo]:
        for _, row in df.iterrows():
            order = {
                "symbol": row['symbol'],
                "date": row['order_execution_time'],
                "type": row['trade_type'].upper(),
                "qty": row['quantity'],
                "price": row['price'],
                "exchange": row['exchange'],
                "segment": row['segment'],
                "order_id": str(row['order_id']),
                "trade_id": str(row['trade_id'])
            }
            orders.append(order)
            
    df_orders = pd.DataFrame(orders)
    df_orders['date'] = pd.to_datetime(df_orders['date'])
    df_orders = df_orders.sort_values('date')
    
    print(f"Found {len(df_orders)} orders.")
    
    print("Uploading to 'orderbook' table...")
    try:
        # using method='multi' for faster inserts
        df_orders.to_sql('orderbook', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        print("Orderbook uploaded successfully.")
    except Exception as e:
        print(f"Error uploading orderbook: {e}")
            
    return df_orders

def process_trades(df_orders):
    print("Processing trades...")
    
    open_trades = {} 
    closed_trades_list = []
    
    # Ensure closure_type column exists
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE closed_trades ADD COLUMN IF NOT EXISTS closure_type text"))
            conn.commit()
            print("Ensured 'closure_type' column exists.")
    except Exception as e:
        print(f"Warning: Could not alter table: {e}")

    for _, order in df_orders.iterrows():
        symbol = order['symbol']
        txn_type = order['type']
        qty = float(order['qty'])
        price = float(order['price'])
        date = order['date']
        exchange = order['exchange']
        
        if symbol in open_trades:
            current_trade = open_trades[symbol]
            
            if current_trade['type'] == txn_type:
                # Accumulation
                total_cost = (current_trade['qty'] * current_trade['avg_price']) + (qty * price)
                new_qty = current_trade['qty'] + qty
                new_avg_price = total_cost / new_qty
                
                current_trade['qty'] = new_qty
                current_trade['avg_price'] = new_avg_price
                
                # Update Max Exposure
                if current_trade['qty'] > current_trade.get('max_exposure', 0):
                    current_trade['max_exposure'] = current_trade['qty']
                    
            else:
                # Reduction/Close
                if qty >= current_trade['qty']:
                    # Full Exit (or Flip)
                    exit_qty = current_trade['qty']
                    remaining_order_qty = qty - exit_qty
                    
                    # Calculate PnL for this exit chunk
                    chunk_pnl = (price - current_trade['avg_price']) * exit_qty if current_trade['type'] == 'BUY' else (current_trade['avg_price'] - price) * exit_qty
                    
                    # Total Lifecycle PnL
                    total_pnl = current_trade.get('accumulated_pnl', 0.0) + chunk_pnl
                    
                    closed_trade = {
                        "symbol": symbol,
                        "qty": current_trade.get('max_exposure', exit_qty), # Reporting Max Exposure as trade size
                        "entry_price": current_trade['avg_price'], # Avg price at close
                        "exit_price": price, # Exit price of final chunk
                        "entry_date": current_trade['entry_date'],
                        "exit_date": date,
                        "pnl": total_pnl,
                        "type": "LONG" if current_trade['type'] == 'BUY' else "SHORT",
                        "exchange": exchange,
                        "closure_type": "FULL"
                    }
                    closed_trades_list.append(closed_trade)
                    del open_trades[symbol]
                    
                    if remaining_order_qty > 0:
                        # Start New Lifecycle (Flip)
                        open_trades[symbol] = {
                            "symbol": symbol,
                            "qty": remaining_order_qty,
                            "avg_price": price,
                            "entry_date": date,
                            "type": txn_type,
                            "exchange": exchange,
                            "accumulated_pnl": 0.0,
                            "max_exposure": remaining_order_qty
                        }
                else:
                    # Partial Exit
                    exit_qty = qty
                    remaining_pos_qty = current_trade['qty'] - exit_qty
                    
                    # Calculate PnL for this chunk
                    chunk_pnl = (price - current_trade['avg_price']) * exit_qty if current_trade['type'] == 'BUY' else (current_trade['avg_price'] - price) * exit_qty
                    
                    # Accumulate PnL, Don't write to DB
                    current_trade['accumulated_pnl'] = current_trade.get('accumulated_pnl', 0.0) + chunk_pnl
                    current_trade['qty'] = remaining_pos_qty
                    
        else:
            # New Open Trade
            open_trades[symbol] = {
                "symbol": symbol,
                "qty": qty,
                "avg_price": price,
                "entry_date": date,
                "type": txn_type,
                "exchange": exchange,
                "accumulated_pnl": 0.0,
                "max_exposure": qty
            }
            
    open_trades_list = []
    for symbol, trade in open_trades.items():
        open_trades_list.append({
            "symbol": trade['symbol'],
            "qty": trade['qty'],
            "avg_price": trade['avg_price'],
            "entry_date": trade['entry_date'],
            "type": "LONG" if trade['type'] == 'BUY' else "SHORT",
            "exchange": trade['exchange']
        })
        
    print(f"Processed {len(closed_trades_list)} closed trades and {len(open_trades_list)} open trades.")
    
    if closed_trades_list:
        print("Uploading closed trades...")
        df_closed = pd.DataFrame(closed_trades_list)
        try:
            df_closed.to_sql('closed_trades', engine, if_exists='append', index=False, method='multi', chunksize=1000)
            print("Closed trades uploaded.")
        except Exception as e:
            print(f"Error uploading closed trades: {e}")

    if open_trades_list:
        print("Uploading open trades...")
        df_open = pd.DataFrame(open_trades_list)
        try:
            # For open trades, we want to replace the current state. 
            # Since this is a backfill, we can truncate and insert? 
            # Or just insert if table is empty.
            # Let's try to append, assuming user cleared tables or it's fresh.
            df_open.to_sql('open_trades', engine, if_exists='append', index=False, method='multi', chunksize=1000)
            print("Open trades uploaded.")
        except Exception as e:
            print(f"Error uploading open trades: {e}")

if __name__ == "__main__":
    EQ_CSV = "/home/fawx/Downloads/tradebook-ZC6915-EQ.csv"
    FO_CSV = "/home/fawx/Downloads/tradebook-ZC6915-FO.csv"
    
    df_orders = upload_orderbook(EQ_CSV, FO_CSV)
    if df_orders is not None:
        process_trades(df_orders)
    
    print("Done!")
