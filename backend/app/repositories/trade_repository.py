from sqlalchemy.orm import Session
import pandas as pd
from app.models.all_models import OpenTrade, ClosedTrade, DailyEquity, TradeConstituent, DailyCost, Journal, Transaction, Orderbook, DailyAccountValue, WeeklyAccountValue
from datetime import datetime

class TradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_open_trades(self):
        return self.db.query(OpenTrade).all()

    def get_partial_closed_trades(self):
        return self.db.query(ClosedTrade).filter(ClosedTrade.closure_type.like('%PARTIAL%')).all()

    def get_transactions(self):
        return self.db.query(Transaction).all()

    def upsert_open_trade(self, trade_data):
        trade = self.db.query(OpenTrade).filter(OpenTrade.symbol == trade_data['symbol']).first()
        if trade:
            for key, value in trade_data.items():
                setattr(trade, key, value)
        else:
            trade = OpenTrade(**trade_data)
            self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def delete_open_trade(self, symbol):
        self.db.query(OpenTrade).filter(OpenTrade.symbol == symbol).delete()
        self.db.commit()

    def add_closed_trade(self, trade_data):
        trade = ClosedTrade(**trade_data)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def apply_trade_operations(self, operations):
        count = 0
        for op in operations:
            action = op['action']
            if action == 'UPSERT_OPEN_TRADE':
                self.upsert_open_trade(op['data'])
                count += 1
            elif action == 'DELETE_OPEN_TRADE':
                self.delete_open_trade(op['symbol'])
                count += 1
            elif action == 'ADD_CLOSED_TRADE':
                self.add_closed_trade(op['data'])
                count += 1
            elif action == 'UPDATE_CLOSED_TRADE':
                trade_id = op['id']
                updates = op['data']
                trade = self.db.query(ClosedTrade).filter(ClosedTrade.id == trade_id).first()
                if trade:
                    for key, value in updates.items():
                        setattr(trade, key, value)
                    self.db.commit()
                    count += 1
            elif action == 'UPDATE_CONSTITUENT':
                const_id = op['id']
                updates = op['data']
                constituent = self.db.query(TradeConstituent).filter(TradeConstituent.id == const_id).first()
                if constituent:
                    for key, value in updates.items():
                        setattr(constituent, key, value)
                    self.db.commit()
                    count += 1
            elif action == 'UPDATE_BASKET_ADD':
                basket_id = op['id']
                amount = op['amount']
                basket = self.db.query(OpenTrade).filter(OpenTrade.id == basket_id).first()
                if basket:
                    basket.avg_price += amount
                    basket.max_exposure = max(basket.max_exposure, int(basket.avg_price))
                    self.db.commit()
                    count += 1
            elif action == 'UPDATE_BASKET_REDUCE':
                basket_id = op['id']
                cost_removed = op['cost_removed']
                pnl_realized = op['pnl_realized']
                basket = self.db.query(OpenTrade).filter(OpenTrade.id == basket_id).first()
                if basket:
                    basket.avg_price -= cost_removed
                    # Update realized PnL for the basket
                    basket.realized_pnl = (basket.realized_pnl or 0.0) + pnl_realized
                    
                    closed_trade_data = {
                        'symbol': basket.symbol,
                        'instrument_token': 0,
                        'qty': 0,
                        'entry_price': 0,
                        'exit_price': 0,
                        'entry_date': basket.entry_date,
                        'exit_date': datetime.now(),
                        'pnl': pnl_realized,
                        'type': 'BASKET',
                        'exchange': 'MULTI',
                        'closure_type': 'PARTIAL_BASKET',
                        'product': 'MIS',
                        'strategy_type': basket.strategy_type,
                        'is_basket': 1,
                        'basket_id': basket.id
                    }
                    self.add_closed_trade(closed_trade_data)
                    self.db.commit()
                    count += 1
        return count

    def process_orders(self, orders_df):
        """
        Syncs orders from Zerodha to local DB incrementally.
        Handles new orders to update open/closed trades.
        """
        if orders_df.empty:
            return 0
            
        # 1. Filter for COMPLETE orders only
        complete_orders = orders_df[orders_df['status'] == 'COMPLETE'].copy()
        if complete_orders.empty:
            return 0
            
        # 2. Get existing order IDs to avoid duplicates
        existing_order_ids = set(
            flat[0] for flat in self.db.query(Orderbook.order_id).all()
        )
        
        # 3. Process new orders
        count = 0
        # Sort by timestamp to process in order
        complete_orders['order_timestamp'] = pd.to_datetime(complete_orders['order_timestamp'])
        complete_orders = complete_orders.sort_values('order_timestamp')
        
        for _, row in complete_orders.iterrows():
            order_id = row['order_id']
            if order_id in existing_order_ids:
                continue
                
            # Add to Orderbook
            order_record = Orderbook(
                order_id=order_id,
                exchange_order_id=row.get('exchange_order_id'),
                status=row['status'],
                order_timestamp=row['order_timestamp'],
                exchange_timestamp=pd.to_datetime(row.get('exchange_timestamp')) if row.get('exchange_timestamp') else None,
                transaction_type=row['transaction_type'],
                tradingsymbol=row['tradingsymbol'],
                instrument_token=row['instrument_token'],
                product=row['product'],
                quantity=row['quantity'],
                average_price=row['average_price'],
                filled_quantity=row['filled_quantity'],
                pending_quantity=row['pending_quantity'],
                cancelled_quantity=row['cancelled_quantity'],
                parent_order_id=row.get('parent_order_id'),
                tag=row.get('tag')
            )
            self.db.add(order_record)
            # Dedup Check: Check if this order was already manually entered
            # We look for a trade with same Symbol, Type, Qty, and approx Time (within 15 mins)
            # This prevents double-counting if the user manually added the trade before syncing
            
            is_duplicate = False
            time_window = timedelta(minutes=15)
            check_type = 'LONG' if row['transaction_type'] == 'BUY' else 'SHORT'
            check_time = row['order_timestamp']
            
            # Check OpenTrades
            existing_trade = self.db.query(OpenTrade).filter(
                OpenTrade.symbol == row['tradingsymbol'],
                OpenTrade.type == check_type,
                OpenTrade.qty == row['quantity'],
                OpenTrade.entry_date >= check_time - time_window,
                OpenTrade.entry_date <= check_time + time_window
            ).first()
            
            if existing_trade:
                is_duplicate = True
                
            # Check Constituents
            if not is_duplicate:
                existing_const = self.db.query(TradeConstituent).filter(
                    TradeConstituent.symbol == row['tradingsymbol'],
                    TradeConstituent.type == check_type,
                    TradeConstituent.qty == row['quantity'],
                    TradeConstituent.entry_date >= check_time - time_window,
                    TradeConstituent.entry_date <= check_time + time_window
                ).first()
                if existing_const:
                    is_duplicate = True
            
            if is_duplicate:
                print(f"Skipping duplicate manual trade for order {order_id}")
                # We still add it to Orderbook (done above) so we don't re-process it
                # But we skip the trade logic
                continue

            # Trade Logic
            symbol = row['tradingsymbol']
            qty = row['quantity']
            price = row['average_price']
            txn_type = row['transaction_type'] # BUY or SELL
            
            # Check if this is a constituent of a basket
            # We join with OpenTrade to ensure we get the active basket
            constituent = self.db.query(TradeConstituent).join(OpenTrade).filter(
                TradeConstituent.symbol == symbol, 
                OpenTrade.is_basket == 1
            ).first()
            
            if constituent:
                # Handle Basket Constituent Logic
                basket = constituent.basket_trade
                
                # Determine if same side (Accumulate) or opposite (Reduce)
                # Constituent type is usually LONG for equity, but could be SHORT for F&O
                is_same_side = (constituent.type == 'LONG' and txn_type == 'BUY') or \
                               (constituent.type == 'SHORT' and txn_type == 'SELL')
                
                if is_same_side:
                    # Accumulate Constituent
                    new_qty = constituent.qty + qty
                    new_avg = ((constituent.qty * constituent.avg_price) + (qty * price)) / new_qty
                    
                    constituent.qty = new_qty
                    constituent.avg_price = new_avg
                    
                    # Update Basket Totals
                    # Add cost of new purchase to basket avg_price (which tracks total cost for baskets)
                    basket.avg_price += (qty * price)
                    basket.max_exposure = max(basket.max_exposure, int(basket.avg_price))
                    
                else:
                    # Reduce / Close Constituent
                    if qty < constituent.qty:
                        # Partial Reduction
                        # Calculate PnL
                        pnl = 0
                        if constituent.type == 'LONG':
                            pnl = (price - constituent.avg_price) * qty
                        else:
                            pnl = (constituent.avg_price - price) * qty
                            
                        # Update Basket Realized PnL
                        basket.realized_pnl = (basket.realized_pnl or 0.0) + pnl
                        
                        # Create ClosedTrade for the leg (Linked to Basket)
                        closed_trade = ClosedTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=qty,
                            entry_price=constituent.avg_price,
                            exit_price=price,
                            entry_date=constituent.entry_date,
                            exit_date=row['order_timestamp'],
                            pnl=pnl,
                            type=constituent.type,
                            exchange=row['exchange'],
                            closure_type='PARTIAL_BASKET',
                            product=row['product'],
                            strategy_type=basket.strategy_type,
                            is_mtf=basket.is_mtf,
                            is_basket=1,
                            basket_id=basket.id
                        )
                        self.db.add(closed_trade)
                        
                        # Update Constituent
                        constituent.qty -= qty
                        # Remove cost from basket avg_price
                        # We remove the PROPORTIONAL cost of the exited qty
                        cost_removed = qty * constituent.avg_price
                        basket.avg_price -= cost_removed
                        
                    elif qty == constituent.qty:
                        # Full Closure of Leg
                        pnl = 0
                        if constituent.type == 'LONG':
                            pnl = (price - constituent.avg_price) * qty
                        else:
                            pnl = (constituent.avg_price - price) * qty
                            
                        # Update Basket Realized PnL
                        basket.realized_pnl = (basket.realized_pnl or 0.0) + pnl
                        
                        # Create ClosedTrade
                        closed_trade = ClosedTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=qty,
                            entry_price=constituent.avg_price,
                            exit_price=price,
                            entry_date=constituent.entry_date,
                            exit_date=row['order_timestamp'],
                            pnl=pnl,
                            type=constituent.type,
                            exchange=row['exchange'],
                            closure_type='PARTIAL_BASKET', # Still partial basket unless it's the last leg
                            product=row['product'],
                            strategy_type=basket.strategy_type,
                            is_mtf=basket.is_mtf,
                            is_basket=1,
                            basket_id=basket.id
                        )
                        self.db.add(closed_trade)
                        
                        # Remove cost
                        cost_removed = qty * constituent.avg_price
                        basket.avg_price -= cost_removed
                        
                        # Delete Constituent
                        self.db.delete(constituent)
                        
                        # Check if Basket is empty
                        # We need to flush/commit to see the deletion? Or check count - 1
                        # Safe way: Check if this was the last constituent
                        remaining_constituents = self.db.query(TradeConstituent).filter(
                            TradeConstituent.open_trade_id == basket.id,
                            TradeConstituent.id != constituent.id
                        ).count()
                        
                        if remaining_constituents == 0:
                            # Close the Basket Trade itself
                            # Logic: Move OpenTrade to ClosedTrade? 
                            # Or just mark it closed?
                            # Usually we move to ClosedTrade.
                            # But ClosedTrade schema is flat.
                            # For now, let's just delete the OpenTrade and maybe create a summary ClosedTrade?
                            # Or leave it as an empty OpenTrade?
                            # User requirement: "entire basket moves to closed trades only when all constituents are closed"
                            
                            # Let's create a summary ClosedTrade for the Basket
                            # PnL = realized_pnl
                            basket_closed = ClosedTrade(
                                symbol=basket.symbol, # Basket Name
                                instrument_token=basket.instrument_token,
                                qty=basket.qty,
                                entry_price=0, # N/A
                                exit_price=0, # N/A
                                entry_date=basket.entry_date,
                                exit_date=row['order_timestamp'],
                                pnl=basket.realized_pnl,
                                type='BASKET',
                                exchange='MULTI',
                                closure_type='FULL_BASKET',
                                product=basket.product,
                                strategy_type=basket.strategy_type,
                                is_basket=1,
                                realized_pnl=basket.realized_pnl
                            )
                            self.db.add(basket_closed)
                            self.db.delete(basket)
                    
                    else:
                        # Flip logic for constituent? 
                        # Complex. For now, treat as Full Close + New Standalone for remainder?
                        # Or New Constituent?
                        # Let's assume Full Close of Leg + New Standalone Trade for remainder
                        
                        # 1. Full Close Leg
                        pnl = 0
                        if constituent.type == 'LONG':
                            pnl = (price - constituent.avg_price) * constituent.qty
                        else:
                            pnl = (constituent.avg_price - price) * constituent.qty
                            
                        basket.realized_pnl = (basket.realized_pnl or 0.0) + pnl
                        
                        closed_trade = ClosedTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=constituent.qty,
                            entry_price=constituent.avg_price,
                            exit_price=price,
                            entry_date=constituent.entry_date,
                            exit_date=row['order_timestamp'],
                            pnl=pnl,
                            type=constituent.type,
                            exchange=row['exchange'],
                            closure_type='PARTIAL_BASKET',
                            product=row['product'],
                            strategy_type=basket.strategy_type,
                            is_basket=1,
                            basket_id=basket.id
                        )
                        self.db.add(closed_trade)
                        
                        cost_removed = constituent.qty * constituent.avg_price
                        basket.avg_price -= cost_removed
                        self.db.delete(constituent)
                        
                        # 2. New Standalone Trade for remainder
                        remaining_qty = qty - constituent.qty
                        new_trade_type = 'LONG' if txn_type == 'BUY' else 'SHORT'
                        
                        new_trade = OpenTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=remaining_qty,
                            avg_price=price,
                            entry_date=row['order_timestamp'],
                            type=new_trade_type,
                            exchange=row['exchange'],
                            max_exposure=int(remaining_qty * price),
                            product=row['product'],
                            is_mtf=1 if row['product'] == 'MTF' else 0,
                            strategy_type=basket.strategy_type,
                            is_basket=0
                        )
                        self.db.add(new_trade)

            else:
                # Check for existing open trade
                open_trade = self.db.query(OpenTrade).filter(OpenTrade.symbol == symbol).first()
            
            if not open_trade:
                # New Position
                trade_type = 'LONG' if txn_type == 'BUY' else 'SHORT'
                
                # Strategy inference
                strategy_type = 'TRENDING'
                if symbol.endswith('CE') or symbol.endswith('PE'):
                    strategy_type = 'SIDEWAYS'
                elif row['product'] == 'CNC': # Holdings usually investment
                    strategy_type = 'INVESTMENT'
                    
                new_trade = OpenTrade(
                    symbol=symbol,
                    instrument_token=row['instrument_token'],
                    qty=qty,
                    avg_price=price,
                    entry_date=row['order_timestamp'],
                    type=trade_type,
                    exchange=row['exchange'],
                    max_exposure=int(qty * price),
                    product=row['product'],
                    is_mtf=1 if row['product'] == 'MTF' else 0,
                    strategy_type=strategy_type,
                    is_basket=0
                )
                self.db.add(new_trade)
            else:
                # Existing Position - Update Logic
                is_same_side = (open_trade.type == 'LONG' and txn_type == 'BUY') or \
                               (open_trade.type == 'SHORT' and txn_type == 'SELL')
                               
                if is_same_side:
                    # Accumulate
                    new_qty = open_trade.qty + qty
                    new_avg = ((open_trade.qty * open_trade.avg_price) + (qty * price)) / new_qty
                    
                    open_trade.qty = new_qty
                    open_trade.avg_price = new_avg
                    open_trade.max_exposure = max(open_trade.max_exposure, int(new_qty * new_avg))
                else:
                    # Reduce / Close / Flip
                    if qty < open_trade.qty:
                        # Partial Exit
                        # Calculate PnL for the exited portion
                        pnl = 0
                        if open_trade.type == 'LONG':
                            pnl = (price - open_trade.avg_price) * qty
                        else:
                            pnl = (open_trade.avg_price - price) * qty
                            
                        # Create ClosedTrade (PARTIAL)
                        closed_trade = ClosedTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=qty,
                            entry_price=open_trade.avg_price,
                            exit_price=price,
                            entry_date=open_trade.entry_date,
                            exit_date=row['order_timestamp'],
                            pnl=pnl,
                            type=open_trade.type,
                            exchange=row['exchange'],
                            closure_type='PARTIAL',
                            product=row['product'],
                            strategy_type=open_trade.strategy_type,
                            is_mtf=open_trade.is_mtf,
                            is_basket=open_trade.is_basket
                        )
                        self.db.add(closed_trade)
                        
                        # Update OpenTrade
                        open_trade.qty -= qty
                        # Avg price remains same for reduction
                        
                    elif qty == open_trade.qty:
                        # Full Exit
                        pnl = 0
                        if open_trade.type == 'LONG':
                            pnl = (price - open_trade.avg_price) * qty
                        else:
                            pnl = (open_trade.avg_price - price) * qty
                            
                        closed_trade = ClosedTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=qty,
                            entry_price=open_trade.avg_price,
                            exit_price=price,
                            entry_date=open_trade.entry_date,
                            exit_date=row['order_timestamp'],
                            pnl=pnl,
                            type=open_trade.type,
                            exchange=row['exchange'],
                            closure_type='FULL',
                            product=row['product'],
                            strategy_type=open_trade.strategy_type,
                            is_mtf=open_trade.is_mtf,
                            is_basket=open_trade.is_basket,
                            realized_pnl=open_trade.realized_pnl # Carry over any basket realized pnl
                        )
                        self.db.add(closed_trade)
                        self.db.delete(open_trade)
                        
                    else:
                        # Flip (Close current + Open new opposite)
                        # 1. Close current
                        close_qty = open_trade.qty
                        pnl = 0
                        if open_trade.type == 'LONG':
                            pnl = (price - open_trade.avg_price) * close_qty
                        else:
                            pnl = (open_trade.avg_price - price) * close_qty
                            
                        closed_trade = ClosedTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=close_qty,
                            entry_price=open_trade.avg_price,
                            exit_price=price,
                            entry_date=open_trade.entry_date,
                            exit_date=row['order_timestamp'],
                            pnl=pnl,
                            type=open_trade.type,
                            exchange=row['exchange'],
                            closure_type='FULL_FLIP',
                            product=row['product'],
                            strategy_type=open_trade.strategy_type,
                            is_mtf=open_trade.is_mtf,
                            is_basket=open_trade.is_basket,
                            realized_pnl=open_trade.realized_pnl
                        )
                        self.db.add(closed_trade)
                        self.db.delete(open_trade)
                        
                        # 2. Open new opposite
                        remaining_qty = qty - close_qty
                        new_trade_type = 'LONG' if txn_type == 'BUY' else 'SHORT'
                        
                        new_trade = OpenTrade(
                            symbol=symbol,
                            instrument_token=row['instrument_token'],
                            qty=remaining_qty,
                            avg_price=price,
                            entry_date=row['order_timestamp'],
                            type=new_trade_type,
                            exchange=row['exchange'],
                            max_exposure=int(remaining_qty * price),
                            product=row['product'],
                            is_mtf=1 if row['product'] == 'MTF' else 0,
                            strategy_type=open_trade.strategy_type, # Inherit strategy? Or default? Inherit seems safer for flips
                            is_basket=0
                        )
                        self.db.add(new_trade)
            
            count += 1
            
        self.db.commit()
        return count

    def save_daily_equity(self, date, account_value, realized_pnl, unrealized_pnl, total_capital, 
                          nifty50=None, nifty_midcap150=None, nifty_smallcap250=None,
                          open=None, high=None, low=None):
        session = self.db
        try:
            entry = session.query(DailyEquity).filter_by(date=date).first()
            if entry:
                entry.account_value = account_value
                entry.realized_pnl = realized_pnl
                entry.unrealized_pnl = unrealized_pnl
                entry.total_capital = total_capital
                if nifty50 is not None: entry.nifty50 = nifty50
                if nifty_midcap150 is not None: entry.nifty_midcap150 = nifty_midcap150
                if nifty_smallcap250 is not None: entry.nifty_smallcap250 = nifty_smallcap250
                if open is not None: entry.open = open
                if high is not None: entry.high = high
                if low is not None: entry.low = low
            else:
                entry = DailyEquity(
                    date=date,
                    account_value=account_value,
                    realized_pnl=realized_pnl,
                    unrealized_pnl=unrealized_pnl,
                    total_capital=total_capital,
                    nifty50=nifty50,
                    nifty_midcap150=nifty_midcap150,
                    nifty_smallcap250=nifty_smallcap250,
                    open=open if open is not None else account_value,
                    high=high if high is not None else account_value,
                    low=low if low is not None else account_value
                )
                session.add(entry)
            session.commit()
            session.refresh(entry)
        except Exception as e:
            session.rollback()
            raise e

    def get_daily_equity_history(self):
        return self.db.query(DailyEquity).order_by(DailyEquity.date).all()

    def get_unified_trades(self):
        open_trades = self.db.query(OpenTrade).all()
        closed_trades = self.db.query(ClosedTrade).all()
        
        # Calculate Realized PnL per symbol
        realized_pnl_map = {}
        for t in closed_trades:
            if t.symbol not in realized_pnl_map:
                realized_pnl_map[t.symbol] = 0.0
            realized_pnl_map[t.symbol] += (t.pnl or 0.0)
        
        unified = []
        
        for t in closed_trades:
            unified.append({
                'id': f"CLOSED_{t.id}",
                'original_id': t.id,
                'source_table': 'CLOSED',
                'trading_symbol': t.symbol,
                'instrument_token': t.instrument_token,
                'exchange': t.exchange,
                'segment': 'EQ',
                'order_type': t.product,
                'entry_date': t.entry_date,
                'exit_date': t.exit_date,
                'qty': t.qty,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'pnl': t.pnl,
                'status': 'PARTIAL' if t.closure_type and 'PARTIAL' in t.closure_type else 'CLOSED',
                'is_mtf': t.is_mtf,
                'setup_used': t.setup_used,
                'mistakes_made': t.mistakes_made,
                'notes': t.notes,
                'screenshot_path': t.screenshot_path,
                'type': t.type,
                'strategy_type': t.strategy_type,
                'is_basket': getattr(t, 'is_basket', 0),
                'closure_type': t.closure_type,
                'realized_pnl': 0 # Closed trades don't need this field in the same way, or it's just their own PnL
            })
            
        for t in open_trades:
            # Get realized PnL for this symbol
            r_pnl = 0.0
            if getattr(t, 'is_basket', 0) == 1:
                r_pnl = getattr(t, 'realized_pnl', 0.0)
            else:
                r_pnl = realized_pnl_map.get(t.symbol, 0.0)
                
            unified.append({
                'id': f"OPEN_{t.id}",
                'original_id': t.id,
                'source_table': 'OPEN',
                'trading_symbol': t.symbol,
                'instrument_token': t.instrument_token,
                'exchange': t.exchange,
                'segment': 'EQ',
                'order_type': t.product,
                'entry_date': t.entry_date,
                'exit_date': None,
                'qty': t.qty,
                'entry_price': t.avg_price,
                'exit_price': None,
                'pnl': 0,
                'status': 'OPEN',
                'is_mtf': t.is_mtf,
                'setup_used': t.setup_used,
                'mistakes_made': t.mistakes_made,
                'notes': t.notes,
                'screenshot_path': t.screenshot_path,
                'type': t.type,
                'strategy_type': t.strategy_type,
                'is_basket': getattr(t, 'is_basket', 0),
                'stop_loss': getattr(t, 'stop_loss', None),
                'realized_pnl': r_pnl,
                'constituents': [
                    {
                        'id': c.id,
                        'symbol': c.symbol,
                        'instrument_token': c.instrument_token,
                        'qty': c.qty,
                        'avg_price': c.avg_price,
                        'entry_date': c.entry_date,
                        'exchange': c.exchange,
                        'product': c.product,
                        'type': c.type
                    } for c in t.constituents
                ] if getattr(t, 'is_basket', 0) == 1 else []
            })
            
        return unified

    def get_paginated_trades(self, skip: int = 0, limit: int = 100, sort_by: str = 'entry_date', sort_desc: bool = True, status: str = None):
        all_trades = self.get_unified_trades()
        
        # Filter
        if status:
            if status == 'CLOSED':
                all_trades = [t for t in all_trades if t['status'] in ['CLOSED', 'PARTIAL']]
            else:
                all_trades = [t for t in all_trades if t['status'] == status]
            
        # Sort
        reverse = sort_desc
        if sort_by in ['entry_date', 'exit_date', 'pnl', 'entry_price']:
            def sort_key(x):
                val = x.get(sort_by)
                if val is None:
                    return datetime.min if sort_by.endswith('date') else float('-inf')
                return val
            all_trades.sort(key=sort_key, reverse=reverse)
            
        total = len(all_trades)
        paginated = all_trades[skip : skip + limit]
        
        return {
            "data": paginated,
            "total": total,
            "page": (skip // limit) + 1,
            "page_size": limit
        }

    def update_trade(self, composite_id: str, updates: dict):
        parts = composite_id.split('_')
        source = parts[0]
        trade_id = int(parts[1])
        
        if source == 'OPEN':
            trade = self.db.query(OpenTrade).filter(OpenTrade.id == trade_id).first()
        elif source == 'CLOSED':
            trade = self.db.query(ClosedTrade).filter(ClosedTrade.id == trade_id).first()
        else:
            return None
            
        if trade:
            for key, value in updates.items():
                if hasattr(trade, key):
                    setattr(trade, key, value)
            self.db.commit()
            self.db.refresh(trade)
        return trade

    def _get_lot_size(self, symbol):
        """
        Returns the lot size for a given symbol.
        Tries to fetch from InstrumentService cache first.
        Falls back to hardcoded values for major indices.
        """
        # 1. Try Dynamic Lookup
        from app.services.instrument_service import InstrumentService
        instrument_service = InstrumentService()
        lot_size = instrument_service.get_lot_size(symbol)
        
        if lot_size is not None:
            return int(lot_size)

        # 2. Fallback to Hardcoded
        symbol = symbol.upper()
        if symbol.startswith('NIFTY'):
            if 'BANK' in symbol: return 15 # BANKNIFTY
            if 'FIN' in symbol: return 40 # FINNIFTY
            if 'MID' in symbol: return 50 # MIDCPNIFTY
            return 75 # NIFTY 50
        if symbol.startswith('BANKNIFTY'): return 15
        if symbol.startswith('FINNIFTY'): return 40
        if symbol.startswith('MIDCPNIFTY'): return 50
        if symbol.startswith('SENSEX'): return 10
        if symbol.startswith('BANKEX'): return 15
        
        # Default to 1 for stocks or unknown
        return 1

    def create_basket(self, name: str, trade_ids: list, strategy_type: str = 'TRENDING'):
        trades = self.db.query(OpenTrade).filter(OpenTrade.id.in_(trade_ids)).with_for_update().all()
        if not trades:
            return None
            
        total_invested = sum(t.qty * t.avg_price for t in trades)
        min_entry_date = min(t.entry_date for t in trades)
        
        # Calculate basket quantity based on lots
        if trades:
            total_lots = 0
            for t in trades:
                lot_size = self._get_lot_size(t.symbol)
                # Calculate lots for this constituent
                # We assume qty is a multiple of lot_size, but we use float division just in case
                lots = t.qty / lot_size
                total_lots += lots
            
            avg_lots = total_lots / len(trades)
            basket_qty = max(1, int(avg_lots)) # Floor value
        else:
            basket_qty = 1
            
        # Adjust average price to be per-unit (per basket lot)
        # If basket_qty is 1 (meaning 1 lot of the basket), the price is the total cost of that 1 lot.
        # Wait, usually "Price" for a basket is not very meaningful unless normalized.
        # But if we say Qty = 1 (lot), then Price = Total Investment makes sense.
        # If Qty = 2 (lots), Price = Total / 2.
        basket_avg_price = total_invested / basket_qty
        
        basket_trade = OpenTrade(
            symbol=name,
            instrument_token=0, 
            qty=basket_qty,
            avg_price=basket_avg_price,
            entry_date=min_entry_date,
            type='BASKET',
            exchange='MULTI',
            max_exposure=int(total_invested),
            product='MIS', 
            strategy_type=strategy_type,
            is_basket=1
        )
        self.db.add(basket_trade)
        self.db.flush()
        
        for t in trades:
            constituent = TradeConstituent(
                open_trade_id=basket_trade.id,
                symbol=t.symbol,
                instrument_token=t.instrument_token,
                qty=t.qty,
                avg_price=t.avg_price,
                entry_date=t.entry_date,
                exchange=t.exchange,
                product=t.product,
                type=t.type
            )
            self.db.add(constituent)
            self.db.delete(t)
            
        self.db.commit()
        self.db.refresh(basket_trade)
        return basket_trade

    def add_to_basket(self, basket_id: int, trade_ids: list):
        """
        Add existing open trades to an existing basket.
        """
        # 1. Fetch Basket
        basket = self.db.query(OpenTrade).filter(OpenTrade.id == basket_id, OpenTrade.is_basket == 1).with_for_update().first()
        if not basket:
            return None

        # 2. Fetch Trades to Add
        new_trades = self.db.query(OpenTrade).filter(OpenTrade.id.in_(trade_ids)).with_for_update().all()
        if not new_trades:
            return None

        # 3. Calculate New Totals
        # Current Basket Stats
        # Note: basket.avg_price is per-unit (per lot). Total invested = avg_price * qty
        current_invested = basket.avg_price * basket.qty
        
        # New Trades Stats
        new_invested = sum(t.qty * t.avg_price for t in new_trades)
        
        # Calculate Lots
        # We need to recalculate total lots for the *entire* basket (old + new constituents)
        # But we don't have easy access to old constituents' lot sizes unless we query them.
        # However, we know the current basket_qty is the "average lots" of the existing constituents.
        # Let's approximate: 
        # Total Lots = (Current Basket Qty * Num Old Constituents) + (New Trades Lots)
        # Wait, "Basket Qty" is stored as the average lots.
        # So we need the count of existing constituents to reverse engineer.
        
        existing_constituents_count = self.db.query(TradeConstituent).filter(TradeConstituent.open_trade_id == basket.id).count()
        current_total_lots = basket.qty * existing_constituents_count
        
        new_trades_lots = 0
        for t in new_trades:
            lot_size = self._get_lot_size(t.symbol)
            new_trades_lots += (t.qty / lot_size)
            
        total_lots = current_total_lots + new_trades_lots
        total_constituents = existing_constituents_count + len(new_trades)
        
        new_basket_qty = max(1, int(total_lots / total_constituents))
        
        # New Average Price (Per Unit)
        total_invested_final = current_invested + new_invested
        new_avg_price = total_invested_final / new_basket_qty
        
        # 4. Update Basket
        basket.qty = new_basket_qty
        basket.avg_price = new_avg_price
        basket.max_exposure = int(total_invested_final) # Update max exposure
        
        # 5. Move Trades to Constituents
        for t in new_trades:
            constituent = TradeConstituent(
                open_trade_id=basket.id,
                symbol=t.symbol,
                instrument_token=t.instrument_token,
                qty=t.qty,
                avg_price=t.avg_price,
                entry_date=t.entry_date,
                exchange=t.exchange,
                product=t.product,
                type=t.type
            )
            self.db.add(constituent)
            self.db.delete(t)
            
        self.db.commit()
        self.db.refresh(basket)
        return basket

    def get_basket_constituents(self, open_trade_id=None, closed_trade_id=None):
        query = self.db.query(TradeConstituent)
        if open_trade_id:
            query = query.filter(TradeConstituent.open_trade_id == open_trade_id)
        if closed_trade_id:
            query = query.filter(TradeConstituent.closed_trade_id == closed_trade_id)
        return query.all()

    def get_all_order_ids(self):
        """Returns a set of all processed order IDs."""
        orders = self.db.query(Orderbook.order_id).all()
        return {o[0] for o in orders}

    def save_orders(self, orders_df):
        """Bulk saves orders to the Orderbook table."""
        if orders_df.empty:
            return
            
        orders_to_add = []
        for _, row in orders_df.iterrows():
            # Check if order already exists (double check)
            existing = self.db.query(Orderbook).filter(Orderbook.order_id == row['order_id']).first()
            if existing:
                continue
                
            order = Orderbook(
                order_id=row['order_id'],
                exchange_order_id=row.get('exchange_order_id'),
                status=row['status'],
                order_timestamp=pd.to_datetime(row['order_timestamp']),
                exchange_timestamp=pd.to_datetime(row.get('exchange_timestamp')) if row.get('exchange_timestamp') else None,
                transaction_type=row['transaction_type'],
                tradingsymbol=row['tradingsymbol'],
                instrument_token=row['instrument_token'],
                product=row['product'],
                quantity=row['quantity'],
                average_price=row['average_price'],
                filled_quantity=row['filled_quantity'],
                pending_quantity=row['pending_quantity'],
                cancelled_quantity=row['cancelled_quantity'],
                parent_order_id=row.get('parent_order_id'),
                tag=row.get('tag')
            )
            orders_to_add.append(order)
            
        if orders_to_add:
            self.db.add_all(orders_to_add)
            self.db.commit()

    def get_daily_ohlc_from_candles(self):
        """Aggregates AccountValue into daily OHLC."""
        from sqlalchemy import func, cast, Date
        from app.models.all_models import AccountValue
        
        # We need to group by date(timestamp)
        # SQLite: date(timestamp)
        # Postgres: cast(timestamp as Date)
        # Since we are using SQLite (based on previous errors), we use func.date
        
        # Actually, let's try a generic approach or check dialect
        # For now assuming SQLite as per previous 'sqlite3' command usage attempt
        
        # Query: Date, Open (first), High (max), Low (min), Close (last)
        # Getting first/last in SQL group by is tricky without window functions.
        # Simpler approach: Fetch all candles and aggregate in Python (pandas) since dataset is small (146 rows).
        
        candles = self.db.query(AccountValue).all()
        if not candles:
            return {}
            
        data = []
        for c in candles:
            data.append({
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close
            })
            
        df = pd.DataFrame(data)
        df['date'] = df['timestamp'].dt.date
        
        daily = df.groupby('date').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).reset_index()
        
        # Convert to dict: {date_obj: {open, high, low, close}}
        result = {}
        for _, row in daily.iterrows():
            result[row['date']] = {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            }
            
        return result

    def aggregate_account_values(self):
        """
        Aggregates AccountValue records into DailyAccountValue and WeeklyAccountValue tables.
        This implements the Lambda Architecture batch layer.
        """
        from app.models.all_models import AccountValue, DailyAccountValue, WeeklyAccountValue
        from sqlalchemy import func
        
        # 1. Fetch all raw data (for now, in production we might filter by last aggregation time)
        raw_data = self.db.query(AccountValue).order_by(AccountValue.timestamp).all()
        if not raw_data:
            return {"daily": 0, "weekly": 0}
            
        # 2. Process in Python (Pandas is easier for resampling)
        df = pd.DataFrame([{
            'timestamp': r.timestamp,
            'open': r.open,
            'high': r.high,
            'low': r.low,
            'close': r.close
        } for r in raw_data])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # --- Daily Aggregation ---
        daily_df = df.resample('D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        daily_objects = []
        for date, row in daily_df.iterrows():
            daily_objects.append({
                'date': date.date(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
        # Bulk Upsert Daily
        # SQLAlchemy doesn't have a native cross-db bulk upsert, so we'll do delete-insert for simplicity 
        # or merge one by one. Merge is safer.
        daily_count = 0
        for obj in daily_objects:
            existing = self.db.query(DailyAccountValue).filter(DailyAccountValue.date == obj['date']).first()
            if existing:
                existing.open = obj['open']
                existing.high = obj['high']
                existing.low = obj['low']
                existing.close = obj['close']
            else:
                self.db.add(DailyAccountValue(**obj))
            daily_count += 1
            
        # --- Weekly Aggregation ---
        # Resample 'W-MON' (Weekly starting Monday)
        weekly_df = df.resample('W-MON', closed='left', label='left').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        }).dropna()
        
        weekly_objects = []
        for date, row in weekly_df.iterrows():
            weekly_objects.append({
                'week_start_date': date.date(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
        weekly_count = 0
        for obj in weekly_objects:
            existing = self.db.query(WeeklyAccountValue).filter(WeeklyAccountValue.week_start_date == obj['week_start_date']).first()
            if existing:
                existing.open = obj['open']
                existing.high = obj['high']
                existing.low = obj['low']
                existing.close = obj['close']
            else:
                self.db.add(WeeklyAccountValue(**obj))
            weekly_count += 1
            
        self.db.commit()
        return {"daily": daily_count, "weekly": weekly_count}
