from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class KiteClient:
    def __init__(self, api_key, api_secret=None, request_token=None, access_token=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=api_key)
        
        if access_token:
            self.kite.set_access_token(access_token)
        elif request_token and api_secret:
            try:
                data = self.kite.generate_session(request_token, api_secret=api_secret)
                self.kite.set_access_token(data["access_token"])
                self.access_token = data["access_token"]
            except Exception as e:
                logger.error(f"Error generating session: {e}")
                raise e
        else:
            # If no tokens provided, we might be in a state where we just want to initialize the client
            # but can't make calls yet.
            pass

    def get_login_url(self):
        return self.kite.login_url()

    def fetch_orders(self):
        """Fetches orders and returns a DataFrame."""
        try:
            orders = self.kite.orders()
            return pd.DataFrame(orders)
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return pd.DataFrame()

    def fetch_positions(self):
        """Fetches positions and returns a DataFrame."""
        try:
            positions = self.kite.positions()
            return pd.DataFrame(positions['net']) # Using net positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return pd.DataFrame()

    def fetch_ltp(self, instruments):
        """
        Fetch LTP for a list of instruments (e.g., ['NSE:INFY', 'BSE:SENSEX'])
        """
        if not self.kite:
            return {}
        try:
            quote = self.kite.quote(instruments)
            ltp_map = {k: v['last_price'] for k, v in quote.items()}
            return ltp_map
        except Exception as e:
            print(f"Error fetching LTP: {e}")
            return {}

    def fetch_indices_ltp(self):
        """
        Fetch LTP for Nifty 50, Nifty Midcap 150, Nifty Smallcap 250
        """
        # Symbols might vary. Standard NSE indices:
        # Nifty 50: NSE:NIFTY 50
        # Nifty Midcap 150: NSE:NIFTY MIDCAP 150
        # Nifty Smallcap 250: NSE:NIFTY SMALLCAP 250
        # Note: Kite symbols for indices often have spaces.
        
        indices = [
            "NSE:NIFTY 50",
            "NSE:NIFTY MIDCAP 150",
            "NSE:NIFTY SMALLCAP 250"
        ]
        
        return self.fetch_ltp(indices)

    def save_access_token(self, token, filepath="access_token.json"):
        import json
        try:
            with open(filepath, "w") as f:
                json.dump({"access_token": token, "timestamp": str(datetime.now())}, f)
        except Exception as e:
            logger.error(f"Error saving access token: {e}")

    @staticmethod
    def load_access_token(filepath="access_token.json"):
        import json
        import os
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    return data.get("access_token")
            except Exception as e:
                logger.error(f"Error loading access token: {e}")
        return None

    def validate_token(self):
        try:
            self.kite.profile()
            return True
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False

    def process_trades(self, orders_df, db_open_trades=None):
        """
        Process orders to identify distinct trades (FIFO matching).
        Returns a list of operations to be performed on the database.
        """
        if orders_df.empty:
            return []

        # Filter for filled orders only
        filled_orders = orders_df[orders_df['status'] == 'COMPLETE'].copy()
        filled_orders['order_timestamp'] = pd.to_datetime(filled_orders['order_timestamp'])
        filled_orders = filled_orders.sort_values('order_timestamp')

        operations = []
        
        # Initialize open positions from DB
        # Key: symbol, Value: dict with trade details
        open_positions = {}
        if db_open_trades:
            for trade in db_open_trades:
                open_positions[trade.symbol] = {
                    'symbol': trade.symbol,
                    'qty': trade.qty,
                    'avg_price': trade.avg_price,
                    'entry_date': trade.entry_date,
                    'type': trade.type,
                    'exchange': trade.exchange,
                    'max_exposure': trade.max_exposure,
                    'instrument_token': trade.instrument_token,
                    'product': trade.product,
                    'strategy_type': getattr(trade, 'strategy_type', 'TRENDING')
                }

        for _, order in filled_orders.iterrows():
            symbol = order['tradingsymbol']
            transaction_type = order['transaction_type'] # BUY/SELL
            qty = order['quantity']
            price = order['average_price']
            timestamp = order['order_timestamp']
            exchange = order['exchange']
            product = order['product']
            token = order['instrument_token']
            
            # Determine Strategy Type
            # Default: TRENDING. If OPT (Options), then SIDEWAYS.
            # We can check symbol suffix or segment if available. 
            # Kite orders have 'instrument_token' and 'tradingsymbol'.
            # Usually 'NFO' exchange orders are F&O.
            # If tradingsymbol ends with 'CE' or 'PE', it's an option.
            # Or if we had segment info. 
            # Let's use simple heuristic on symbol for now as segment isn't in order dict directly 
            # (though fetch_orders might have it, let's assume we rely on symbol).
            
            strategy_type = 'TRENDING'
            if symbol.endswith('CE') or symbol.endswith('PE'):
                strategy_type = 'SIDEWAYS'
            
            # Map Transaction Type to Trade Type (LONG/SHORT)
            # Assuming Equity Delivery (CNC) is Long. Intraday (MIS) can be Short.
            # But for simplicity, let's assume BUY -> LONG, SELL -> SHORT for opening.
            
            if symbol in open_positions:
                current_pos = open_positions[symbol]
                
                # Determine if it's accumulation or reduction
                # Long: BUY is Acc, SELL is Red
                # Short: SELL is Acc, BUY is Red
                
                is_accumulation = False
                if current_pos['type'] == 'LONG' and transaction_type == 'BUY':
                    is_accumulation = True
                elif current_pos['type'] == 'SHORT' and transaction_type == 'SELL':
                    is_accumulation = True
                
                if is_accumulation:
                    # Accumulation
                    total_cost = (current_pos['qty'] * current_pos['avg_price']) + (qty * price)
                    new_qty = current_pos['qty'] + qty
                    new_avg_price = total_cost / new_qty
                    
                    current_pos['qty'] = new_qty
                    current_pos['avg_price'] = new_avg_price
                    if new_qty > current_pos['max_exposure']:
                        current_pos['max_exposure'] = new_qty
                        
                    operations.append({
                        'action': 'UPSERT_OPEN_TRADE',
                        'data': current_pos.copy()
                    })
                    
                else:
                    # Reduction/Exit
                    if qty >= current_pos['qty']:
                        # Full Exit (or Flip)
                        exit_qty = current_pos['qty']
                        remaining_order_qty = qty - exit_qty
                        
                        # Calculate PnL
                        pnl = (price - current_pos['avg_price']) * exit_qty if current_pos['type'] == 'LONG' else (current_pos['avg_price'] - price) * exit_qty
                        
                        closed_trade = {
                            'symbol': symbol,
                            'instrument_token': token,
                            'qty': current_pos['max_exposure'], # Reporting Max Exposure as per user request? Or just exit qty? User code used max_exposure.
                            # Actually, user code: "qty": current_trade.get('max_exposure', exit_qty)
                            # Let's stick to that.
                            'entry_price': current_pos['avg_price'],
                            'exit_price': price,
                            'entry_date': current_pos['entry_date'],
                            'exit_date': timestamp,
                            'pnl': pnl,
                            'type': current_pos['type'],
                            'exchange': exchange,
                            'closure_type': 'FULL',
                            'product': product,
                            'strategy_type': current_pos.get('strategy_type', strategy_type)
                        }
                        operations.append({
                            'action': 'ADD_CLOSED_TRADE',
                            'data': closed_trade
                        })
                        
                        operations.append({
                            'action': 'DELETE_OPEN_TRADE',
                            'symbol': symbol
                        })
                        
                        del open_positions[symbol]
                        
                        # Flip Logic
                        if remaining_order_qty > 0:
                            new_type = 'SHORT' if transaction_type == 'SELL' else 'LONG'
                            new_trade = {
                                'symbol': symbol,
                                'instrument_token': token,
                                'qty': remaining_order_qty,
                                'avg_price': price,
                                'entry_date': timestamp,
                                'type': new_type,
                                'exchange': exchange,
                                'max_exposure': remaining_order_qty,
                                'product': product,
                                'strategy_type': strategy_type
                            }
                            open_positions[symbol] = new_trade
                            operations.append({
                                'action': 'UPSERT_OPEN_TRADE',
                                'data': new_trade
                            })
                            
                    else:
                        # Partial Exit
                        exit_qty = qty
                        remaining_pos_qty = current_pos['qty'] - exit_qty
                        
                        pnl = (price - current_pos['avg_price']) * exit_qty if current_pos['type'] == 'LONG' else (current_pos['avg_price'] - price) * exit_qty
                        
                        # Update Open Trade
                        current_pos['qty'] = remaining_pos_qty
                        operations.append({
                            'action': 'UPSERT_OPEN_TRADE',
                            'data': current_pos.copy()
                        })
                        
                        # Create Closed Trade (Partial)
                        closed_trade = {
                            'symbol': symbol,
                            'instrument_token': token,
                            'qty': exit_qty,
                            'entry_price': current_pos['avg_price'],
                            'exit_price': price,
                            'entry_date': current_pos['entry_date'],
                            'exit_date': timestamp,
                            'pnl': pnl,
                            'type': current_pos['type'],
                            'exchange': exchange,
                            'closure_type': 'PARTIAL',
                            'product': product,
                            'strategy_type': current_pos.get('strategy_type', strategy_type)
                        }
                        operations.append({
                            'action': 'ADD_CLOSED_TRADE',
                            'data': closed_trade
                        })
                        
            else:
                # New Position
                new_type = 'LONG' if transaction_type == 'BUY' else 'SHORT'
                new_trade = {
                    'symbol': symbol,
                    'instrument_token': token,
                    'qty': qty,
                    'avg_price': price,
                    'entry_date': timestamp,
                    'type': new_type,
                    'exchange': exchange,
                    'max_exposure': qty,
                    'product': product,
                    'strategy_type': strategy_type
                }
                open_positions[symbol] = new_trade
                operations.append({
                    'action': 'UPSERT_OPEN_TRADE',
                    'data': new_trade
                })

        return operations
