
from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime
from database.connection import Base
from datetime import datetime

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    instrument_token = Column(Integer, index=True)
    trading_symbol = Column(String, index=True)
    exchange = Column(String)
    segment = Column(String)  # EQ, FUT, OPT
    order_type = Column(String)  # CNC, MIS, NRML, MTF
    entry_date = Column(DateTime)
    exit_date = Column(DateTime)
    qty = Column(Integer)
    entry_price = Column(Float)
    exit_price = Column(Float)
    pnl = Column(Float)
    setup_used = Column(String, nullable=True)
    mistakes_made = Column(String, nullable=True)  # Comma separated tags
    notes = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    is_mtf = Column(Integer, default=0) # 0 for False, 1 for True. SQLite doesn't have Boolean

class Journal(Base):
    __tablename__ = "journal"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    pre_market_notes = Column(Text, nullable=True)
    post_market_analysis = Column(Text, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    amount = Column(Float) # Positive for Deposit, Negative for Withdrawal
    type = Column(String) # DEPOSIT, WITHDRAWAL
    notes = Column(Text, nullable=True)

class Orderbook(Base):
    __tablename__ = "orderbook"

    order_id = Column(String, primary_key=True, index=True)
    exchange_order_id = Column(String, nullable=True)
    status = Column(String)
    order_timestamp = Column(DateTime)
    exchange_timestamp = Column(DateTime, nullable=True)
    transaction_type = Column(String) # BUY/SELL
    tradingsymbol = Column(String)
    instrument_token = Column(Integer)
    product = Column(String)
    quantity = Column(Integer)
    average_price = Column(Float)
    filled_quantity = Column(Integer)
    pending_quantity = Column(Integer)
    cancelled_quantity = Column(Integer)
    parent_order_id = Column(String, nullable=True)
    tag = Column(String, nullable=True)
    
    # Additional fields to match backfill if needed, or map them
    # symbol -> tradingsymbol
    # date -> order_timestamp
    # type -> transaction_type
    # qty -> quantity
    # price -> average_price

class OpenTrade(Base):
    __tablename__ = "open_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True) # tradingsymbol
    instrument_token = Column(Integer)
    qty = Column(Integer)
    avg_price = Column(Float)
    entry_date = Column(DateTime)
    type = Column(String) # LONG/SHORT
    exchange = Column(String)
    max_exposure = Column(Integer, default=0)
    product = Column(String) # CNC/MIS etc
    
    # Journal Fields
    setup_used = Column(String, nullable=True)
    mistakes_made = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    is_mtf = Column(Integer, default=0)
    strategy_type = Column(String, default='TRENDING') # TRENDING/SIDEWAYS

class ClosedTrade(Base):
    __tablename__ = "closed_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    instrument_token = Column(Integer)
    qty = Column(Integer)
    entry_price = Column(Float)
    exit_price = Column(Float)
    entry_date = Column(DateTime)
    exit_date = Column(DateTime)
    pnl = Column(Float)
    type = Column(String) # LONG/SHORT
    exchange = Column(String)
    closure_type = Column(String) # FULL/PARTIAL
    product = Column(String)
    
    # Journal Fields
    setup_used = Column(String, nullable=True)
    mistakes_made = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    is_mtf = Column(Integer, default=0)
    strategy_type = Column(String, default='TRENDING') # TRENDING/SIDEWAYS

class DailyEquity(Base):
    __tablename__ = "daily_equity"
    
    date = Column(Date, primary_key=True)
    account_value = Column(Float)
    realized_pnl = Column(Float)
    unrealized_pnl = Column(Float)
    total_capital = Column(Float)
    nifty50 = Column(Float, nullable=True)
    nifty_midcap150 = Column(Float, nullable=True)
    nifty_smallcap250 = Column(Float, nullable=True)
