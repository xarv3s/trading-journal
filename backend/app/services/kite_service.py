from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import os

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
            pass

    def get_login_url(self):
        return self.kite.login_url()

    def fetch_orders(self):
        try:
            orders = self.kite.orders()
            return pd.DataFrame(orders)
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return pd.DataFrame()

    def fetch_positions(self):
        try:
            positions = self.kite.positions()
            return pd.DataFrame(positions['net'])
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return pd.DataFrame()

    def fetch_ltp(self, instruments):
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
        indices = [
            "NSE:NIFTY 50",
            "NSE:NIFTY MIDCAP 150",
            "NSE:NIFTY SMALLCAP 250"
        ]
        return self.fetch_ltp(indices)

    def save_access_token(self, token, filepath="access_token.json"):
        try:
            with open(filepath, "w") as f:
                json.dump({"access_token": token, "timestamp": str(datetime.now())}, f)
        except Exception as e:
            logger.error(f"Error saving access token: {e}")

    @staticmethod
    def load_access_token(filepath="access_token.json"):
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

    def process_trades(self, orders_df, db_open_trades=None, db_constituents=None, db_closed_trades=None):
        if orders_df.empty:
            return []

        filled_orders = orders_df[orders_df['status'] == 'COMPLETE'].copy()
        filled_orders['order_timestamp'] = pd.to_datetime(filled_orders['order_timestamp'])
        filled_orders = filled_orders.sort_values('order_timestamp')

        operations = []
        open_positions = {}
        basket_constituents = {}
        partial_closed_trades = {}
        
        if db_open_trades:
            for trade in db_open_trades:
                if getattr(trade, 'is_basket', 0) == 1:
                    pass
                else:
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
                        'strategy_type': getattr(trade, 'strategy_type', 'TRENDING'),
                        'is_basket': 0,
                        'id': trade.id
                    }

        if db_constituents:
            for c in db_constituents:
                if c.open_trade_id:
                    basket_constituents[c.symbol] = {
                        'basket_id': c.open_trade_id,
                        'data': {
                            'symbol': c.symbol,
                            'qty': c.qty,
                            'avg_price': c.avg_price,
                            'entry_date': c.entry_date,
                            'exchange': c.exchange,
                            'product': c.product,
                            'id': c.id
                        }
                    }

        if db_closed_trades:
            for t in db_closed_trades:
                # Only consider PARTIAL trades for merging
                if t.closure_type and 'PARTIAL' in t.closure_type:
                    partial_closed_trades[t.symbol] = {
                        'id': t.id,
                        'qty': t.qty,
                        'entry_price': t.entry_price,
                        'exit_price': t.exit_price,
                        'pnl': t.pnl,
                        'closure_type': t.closure_type,
                        'exit_date': t.exit_date
                    }

        for _, order in filled_orders.iterrows():
            symbol = order['tradingsymbol']
            transaction_type = order['transaction_type']
            qty = order['quantity']
            price = order['average_price']
            timestamp = order['order_timestamp']
            exchange = order['exchange']
            product = order['product']
            token = order['instrument_token']
            
            strategy_type = 'TRENDING'
            if symbol.endswith('CE') or symbol.endswith('PE'):
                strategy_type = 'SIDEWAYS'
            
            if symbol in basket_constituents:
                const_info = basket_constituents[symbol]
                basket_id = const_info['basket_id']
                current_pos = const_info['data']
                
                is_accumulation = False
                if transaction_type == 'BUY':
                    is_accumulation = True
                
                if is_accumulation:
                    total_cost = (current_pos['qty'] * current_pos['avg_price']) + (qty * price)
                    new_qty = current_pos['qty'] + qty
                    new_avg_price = total_cost / new_qty
                    
                    current_pos['qty'] = new_qty
                    current_pos['avg_price'] = new_avg_price
                    
                    operations.append({
                        'action': 'UPDATE_CONSTITUENT',
                        'id': current_pos['id'],
                        'data': {'qty': new_qty, 'avg_price': new_avg_price}
                    })
                    
                    operations.append({
                        'action': 'UPDATE_BASKET_ADD',
                        'id': basket_id,
                        'amount': qty * price
                    })
                    
                else:
                    exit_qty = min(qty, current_pos['qty'])
                    remaining_qty = current_pos['qty'] - exit_qty
                    pnl = (price - current_pos['avg_price']) * exit_qty
                    
                    operations.append({
                        'action': 'UPDATE_CONSTITUENT',
                        'id': current_pos['id'],
                        'data': {'qty': remaining_qty}
                    })
                    
                    operations.append({
                        'action': 'UPDATE_BASKET_REDUCE',
                        'id': basket_id,
                        'cost_removed': exit_qty * current_pos['avg_price'],
                        'pnl_realized': pnl
                    })
                    
            elif symbol in open_positions:
                current_pos = open_positions[symbol]
                
                is_accumulation = False
                if current_pos['type'] == 'LONG' and transaction_type == 'BUY':
                    is_accumulation = True
                elif current_pos['type'] == 'SHORT' and transaction_type == 'SELL':
                    is_accumulation = True
                
                if is_accumulation:
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
                    # EXIT LOGIC
                    if qty >= current_pos['qty']:
                        # FULL EXIT (of remaining)
                        exit_qty = current_pos['qty']
                        remaining_order_qty = qty - exit_qty
                        
                        pnl = (price - current_pos['avg_price']) * exit_qty if current_pos['type'] == 'LONG' else (current_pos['avg_price'] - price) * exit_qty
                        
                        # Check for existing partial trade to merge
                        if symbol in partial_closed_trades:
                            existing = partial_closed_trades[symbol]
                            
                            new_total_qty = existing['qty'] + exit_qty
                            new_total_pnl = existing['pnl'] + pnl
                            # Weighted average exit price
                            new_exit_price = ((existing['qty'] * existing['exit_price']) + (exit_qty * price)) / new_total_qty
                            # Weighted average entry price
                            new_entry_price = ((existing['qty'] * existing['entry_price']) + (exit_qty * current_pos['avg_price'])) / new_total_qty
                            
                            operations.append({
                                'action': 'UPDATE_CLOSED_TRADE',
                                'id': existing['id'],
                                'data': {
                                    'qty': new_total_qty,
                                    'pnl': new_total_pnl,
                                    'exit_price': new_exit_price,
                                    'entry_price': new_entry_price,
                                    'closure_type': 'FULL',
                                    'exit_date': timestamp
                                }
                            })
                            # Remove from partials as it is now FULL
                            del partial_closed_trades[symbol]
                            
                        else:
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
                        # PARTIAL EXIT
                        exit_qty = qty
                        remaining_pos_qty = current_pos['qty'] - exit_qty
                        
                        pnl = (price - current_pos['avg_price']) * exit_qty if current_pos['type'] == 'LONG' else (current_pos['avg_price'] - price) * exit_qty
                        
                        current_pos['qty'] = remaining_pos_qty
                        operations.append({
                            'action': 'UPSERT_OPEN_TRADE',
                            'data': current_pos.copy()
                        })
                        
                        # Check for existing partial trade to merge
                        if symbol in partial_closed_trades:
                            existing = partial_closed_trades[symbol]
                            
                            new_total_qty = existing['qty'] + exit_qty
                            new_total_pnl = existing['pnl'] + pnl
                            new_exit_price = ((existing['qty'] * existing['exit_price']) + (exit_qty * price)) / new_total_qty
                            new_entry_price = ((existing['qty'] * existing['entry_price']) + (exit_qty * current_pos['avg_price'])) / new_total_qty
                            
                            operations.append({
                                'action': 'UPDATE_CLOSED_TRADE',
                                'id': existing['id'],
                                'data': {
                                    'qty': new_total_qty,
                                    'pnl': new_total_pnl,
                                    'exit_price': new_exit_price,
                                    'entry_price': new_entry_price,
                                    'closure_type': 'PARTIAL', # Still partial
                                    'exit_date': timestamp
                                }
                            })
                            # Update local cache
                            partial_closed_trades[symbol]['qty'] = new_total_qty
                            partial_closed_trades[symbol]['pnl'] = new_total_pnl
                            partial_closed_trades[symbol]['exit_price'] = new_exit_price
                            partial_closed_trades[symbol]['entry_price'] = new_entry_price
                            partial_closed_trades[symbol]['exit_date'] = timestamp
                            
                        else:
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
                            # Add to local cache for subsequent orders in same batch
                            # We need an ID for future updates in this batch, but we don't have one yet.
                            # This is a limitation. If we have multiple partial exits in the SAME batch for a NEW partial trade,
                            # we can't merge them easily because we don't have the DB ID.
                            # However, we can track it by symbol in a temporary way or just let them be separate and merge later?
                            # Or better: Just treat the first one as the "existing" one for this batch.
                            # Since we can't generate a DB ID, we can't emit UPDATE_CLOSED_TRADE for the second one.
                            # We would have to emit UPDATE_CLOSED_TRADE for a placeholder? No.
                            # For now, let's assume we won't have multiple partial exits for the SAME symbol in the SAME batch 
                            # that start from scratch. If we do, they will be separate rows. That's acceptable edge case.
                        
            else:
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
                    'is_mtf': 1 if product == 'MTF' else 0,
                    'strategy_type': strategy_type
                }
                open_positions[symbol] = new_trade
                operations.append({
                    'action': 'UPSERT_OPEN_TRADE',
                    'data': new_trade
                })

        return operations

    def place_order(self, tradingsymbol, exchange, transaction_type, quantity, price=None, product='MIS', order_type='LIMIT', variety='regular', trigger_price=None):
        try:
            order_id = self.kite.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price
            )
            logger.info(f"Order placed. ID: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise e

    def place_gtt(self, tradingsymbol, exchange, transaction_type, quantity, price, trigger_price, last_price, product='CNC'):
        try:
            trigger_type = self.kite.GTT_TYPE_SINGLE
            
            orders = [
                {
                    "exchange": exchange,
                    "tradingsymbol": tradingsymbol,
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "order_type": "LIMIT",
                    "product": product,
                    "price": price
                }
            ]
            
            trigger_id = self.kite.place_gtt(
                trigger_type=trigger_type,
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                trigger_values=[trigger_price],
                last_price=last_price,
                orders=orders
            )
            logger.info(f"GTT placed. ID: {trigger_id}")
            return trigger_id
        except Exception as e:
            logger.error(f"Error placing GTT: {e}")
            raise e

    def get_all_instruments(self, exchanges=['NSE', 'NFO']):
        try:
            all_instruments = []
            for exchange in exchanges:
                instruments = self.kite.instruments(exchange)
                all_instruments.extend(instruments)
            return pd.DataFrame(all_instruments)
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            return pd.DataFrame()

    def is_market_open(self):
        try:
            # Use a liquid stock to check market status
            sentinel = "NSE:RELIANCE"
            quote = self.kite.quote(sentinel)
            if sentinel not in quote:
                return False
                
            data = quote[sentinel]
            last_trade_time = data.get('last_trade_time')
            
            if not last_trade_time:
                return False
                
            # Handle timezone if necessary (Kite usually returns naive or IST)
            # We'll assume naive matches system time (IST) or handle aware
            now = datetime.now()
            if last_trade_time.tzinfo:
                import pytz
                now = datetime.now(pytz.timezone('Asia/Kolkata'))
                
            diff = now - last_trade_time
            
            # If last trade was within 5 minutes, market is open
            if diff < timedelta(minutes=5):
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
