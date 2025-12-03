from sqlalchemy.orm import Session
import pandas as pd
from app.models.all_models import OpenTrade, ClosedTrade, DailyEquity, TradeConstituent, DailyCost, Journal, Transaction, Orderbook
from datetime import datetime

class TradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_open_trades(self):
        return self.db.query(OpenTrade).all()

    def get_partial_closed_trades(self):
        return self.db.query(ClosedTrade).filter(ClosedTrade.closure_type.like('%PARTIAL%')).all()

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
                        'is_basket': 1
                    }
                    self.add_closed_trade(closed_trade_data)
                    self.db.commit()
                    count += 1
        return count

    def save_daily_equity(self, date, account_value, realized_pnl, unrealized_pnl, total_capital, 
                          nifty50=None, nifty_midcap150=None, nifty_smallcap250=None):
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
            else:
                entry = DailyEquity(
                    date=date,
                    account_value=account_value,
                    realized_pnl=realized_pnl,
                    unrealized_pnl=unrealized_pnl,
                    total_capital=total_capital,
                    nifty50=nifty50,
                    nifty_midcap150=nifty_midcap150,
                    nifty_smallcap250=nifty_smallcap250
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
                'closure_type': t.closure_type
            })
            
        for t in open_trades:
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
                'stop_loss': getattr(t, 'stop_loss', None)
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

    def create_basket(self, name: str, trade_ids: list, strategy_type: str = 'TRENDING'):
        trades = self.db.query(OpenTrade).filter(OpenTrade.id.in_(trade_ids)).all()
        if not trades:
            return None
            
        total_invested = sum(t.qty * t.avg_price for t in trades)
        min_entry_date = min(t.entry_date for t in trades)
        
        basket_trade = OpenTrade(
            symbol=name,
            instrument_token=0, 
            qty=1,
            avg_price=total_invested,
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
                product=t.product
            )
            self.db.add(constituent)
            self.db.delete(t)
            
        self.db.commit()
        self.db.refresh(basket_trade)
        return basket_trade

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
