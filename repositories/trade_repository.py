from sqlalchemy.orm import Session
import pandas as pd
from database.models import Trade, Journal, Transaction, Orderbook, OpenTrade, ClosedTrade, DailyEquity
from datetime import datetime

class TradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_trade(self, trade_data: dict):
        trade = Trade(**trade_data)
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        return trade

    def get_trades(self, skip: int = 0, limit: int = 100):
        return self.db.query(Trade).offset(skip).limit(limit).all()

    def get_all_trades(self):
        return self.db.query(Trade).all()

    def update_trade(self, trade_id: int, updates: dict):
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()
        if trade:
            for key, value in updates.items():
                setattr(trade, key, value)
            self.db.commit()
            self.db.refresh(trade)
        return trade

    def get_open_trades(self):
        """Fetch all trades where exit_date is None."""
        return self.db.query(Trade).filter(Trade.exit_date == None).all()

    def sync_trades(self, trades_list: list):
        """
        Syncs trades from the service to the database.
        Handles both new trades and updates to existing open trades.
        """
        count = 0
        updated_count = 0
        
        for trade_data in trades_list:
            # Check if it's an update to an existing trade (has 'id')
            if 'id' in trade_data and trade_data['id'] is not None:
                self.update_trade(trade_data['id'], trade_data)
                updated_count += 1
            else:
                # Check for duplicates before creating new
                exists = self.db.query(Trade).filter(
                    Trade.trading_symbol == trade_data['trading_symbol'],
                    Trade.entry_date == trade_data['entry_date'],
                    Trade.exit_date == trade_data['exit_date']
                ).first()

                if not exists:
                    self.create_trade(trade_data)
                    count += 1
                    
        return count, updated_count

    def get_journal_entry(self, date):
        return self.db.query(Journal).filter(Journal.date == date).first()

    def create_or_update_journal(self, date, data):
        entry = self.get_journal_entry(date)
        if not entry:
            entry = Journal(date=date, **data)
            self.db.add(entry)
        else:
            for key, value in data.items():
                setattr(entry, key, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def add_transaction(self, date, amount, type, notes):
        transaction = Transaction(date=date, amount=amount, type=type, notes=notes)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transactions(self):
        return self.db.query(Transaction).order_by(Transaction.date.desc()).all()

    def save_orders(self, orders_df):
        """
        Saves orders from a DataFrame to the database.
        Upserts based on order_id.
        """
        count = 0
        if orders_df.empty:
            return count

        for _, row in orders_df.iterrows():
            # Handle timestamps safely
            order_ts = row['order_timestamp']
            if isinstance(order_ts, str):
                order_ts = pd.to_datetime(order_ts)
            
            exchange_ts = row.get('exchange_timestamp')
            if pd.notnull(exchange_ts):
                if isinstance(exchange_ts, str):
                    exchange_ts = pd.to_datetime(exchange_ts)
            else:
                exchange_ts = None

            order_data = {
                'order_id': row['order_id'],
                'exchange_order_id': row.get('exchange_order_id'),
                'status': row['status'],
                'order_timestamp': order_ts,
                'exchange_timestamp': exchange_ts,
                'transaction_type': row['transaction_type'],
                'tradingsymbol': row['tradingsymbol'],
                'instrument_token': row['instrument_token'],
                'product': row['product'],
                'quantity': row['quantity'],
                'average_price': row['average_price'],
                'filled_quantity': row['filled_quantity'],
                'pending_quantity': row['pending_quantity'],
                'cancelled_quantity': row['cancelled_quantity'],
                'parent_order_id': row.get('parent_order_id'),
                'tag': row.get('tag')
            }
            
            existing_order = self.db.query(Orderbook).filter(Orderbook.order_id == order_data['order_id']).first()
            
            if existing_order:
                for key, value in order_data.items():
                    setattr(existing_order, key, value)
            else:
                new_order = Orderbook(**order_data)
                self.db.add(new_order)
                count += 1
        
        self.db.commit()
        return count

    def get_all_open_trades(self):
        return self.db.query(OpenTrade).all()

    def upsert_open_trade(self, trade_data):
        # Check if exists by symbol (assuming 1 open trade per symbol per user logic, 
        # but wait, user might have multiple? 
        # The backfill logic used a dictionary keyed by symbol, implying 1 open trade per symbol.
        # We will follow that logic.)
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
        """
        Executes a list of operations returned by KiteService.process_trades.
        """
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
        return count

    def save_daily_equity(self, date, account_value, realized_pnl, unrealized_pnl, total_capital, 
                          nifty50=None, nifty_midcap150=None, nifty_smallcap250=None):
        session = self.db
        try:
            # Check if entry exists
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
        # Do not close session here if it's managed externally (dependency injection)
        # But if we must, we should be careful. 
        # Usually with get_db(), the caller manages the session lifecycle or context manager.
        # Here app.py calls next(get_db()), so it's an open session.
        # If we close it, subsequent calls might fail.
        # Let's NOT close it here.

    def get_daily_equity_history(self):
        session = self.db
        try:
            history = session.query(DailyEquity).order_by(DailyEquity.date).all()
            # Convert to dicts for easier serialization if needed, or return model objects directly
            return [h.__dict__ for h in history]
        except Exception as e:
            raise e

    def get_unified_trades(self):
        """
        Fetches both open and closed trades and returns them as a unified list of objects/dicts
        compatible with AnalyticsService.
        """
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
                'segment': 'EQ', # Defaulting to EQ as per current logic
                'order_type': t.product,
                'entry_date': t.entry_date,
                'exit_date': t.exit_date,
                'qty': t.qty,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'pnl': t.pnl,
                'status': 'CLOSED',
                'is_mtf': t.is_mtf,
                'setup_used': t.setup_used,
                'mistakes_made': t.mistakes_made,
                'notes': t.notes,
                'screenshot_path': t.screenshot_path,
                'type': t.type,
                'strategy_type': t.strategy_type
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
                'pnl': 0, # Unrealized
                'status': 'OPEN',
                'is_mtf': t.is_mtf,
                'setup_used': t.setup_used,
                'mistakes_made': t.mistakes_made,
                'notes': t.notes,
                'screenshot_path': t.screenshot_path,
                'type': t.type,
                'strategy_type': t.strategy_type
            })
            
        return unified

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
                # Map fields if necessary, or assume model has them
                if hasattr(trade, key):
                    setattr(trade, key, value)
            self.db.commit()
            self.db.refresh(trade)
        return trade
