from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class OpenTrade(Base):
    __tablename__ = "open_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    instrument_token = Column(Integer)
    qty = Column(Integer)
    avg_price = Column(Float)
    entry_date = Column(DateTime, default=datetime.utcnow)
    type = Column(String) # LONG/SHORT
    exchange = Column(String)
    max_exposure = Column(Integer)
    product = Column(String)
    strategy_type = Column(String, default='TRENDING')
    notes = Column(String, nullable=True)
    setup_used = Column(String, nullable=True)
    mistakes_made = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    is_mtf = Column(Integer, default=0)
    is_basket = Column(Integer, default=0)
    stop_loss = Column(Float, nullable=True)
    realized_pnl = Column(Float, default=0.0)
    
    constituents = relationship("TradeConstituent", back_populates="basket_trade", foreign_keys="TradeConstituent.open_trade_id")

class ClosedTrade(Base):
    __tablename__ = "closed_trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    instrument_token = Column(Integer)
    qty = Column(Integer)
    entry_price = Column(Float)
    exit_price = Column(Float)
    entry_date = Column(DateTime)
    exit_date = Column(DateTime, default=datetime.utcnow)
    pnl = Column(Float)
    type = Column(String) # LONG/SHORT
    exchange = Column(String)
    closure_type = Column(String, default='FULL') # FULL/PARTIAL
    product = Column(String)
    strategy_type = Column(String, default='TRENDING')
    notes = Column(String, nullable=True)
    setup_used = Column(String, nullable=True)
    mistakes_made = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    is_mtf = Column(Integer, default=0)
    is_basket = Column(Integer, default=0)
    basket_id = Column(Integer, nullable=True) # Link to parent basket (OpenTrade ID)
    open_trade_id = Column(Integer, nullable=True) # Link to original trade cycle (OpenTrade ID):

class TradeConstituent(Base):
    __tablename__ = "trade_constituents"
    
    id = Column(Integer, primary_key=True, index=True)
    open_trade_id = Column(Integer, ForeignKey('open_trades.id'), nullable=True)
    closed_trade_id = Column(Integer, ForeignKey('closed_trades.id'), nullable=True)
    
    symbol = Column(String)
    instrument_token = Column(Integer)
    qty = Column(Integer)
    avg_price = Column(Float)
    entry_date = Column(DateTime)
    exchange = Column(String)
    product = Column(String)
    type = Column(String)
    
    basket_trade = relationship("OpenTrade", back_populates="constituents", foreign_keys=[open_trade_id])

class DailyCost(Base):
    __tablename__ = "daily_costs"

    date = Column(Date, primary_key=True)
    brokerage = Column(Float, default=0.0)
    taxes = Column(Float, default=0.0)
    mtf_interest = Column(Float, default=0.0)
    total = Column(Float, default=0.0)

class DailyEquity(Base):
    __tablename__ = "daily_equity"
    
    date = Column(Date, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    account_value = Column(Float) # This acts as Close
    realized_pnl = Column(Float)
    unrealized_pnl = Column(Float)
    total_capital = Column(Float)
    
    nifty50 = Column(Float, nullable=True)
    nifty_midcap150 = Column(Float, nullable=True)
    nifty_smallcap250 = Column(Float, nullable=True)
    
    ema_10 = Column(Float, nullable=True)
    ema_21 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    ema_200 = Column(Float, nullable=True)

class Journal(Base):
    __tablename__ = "journal"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    pre_market_notes = Column(String, nullable=True)
    post_market_analysis = Column(String, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    amount = Column(Float)
    type = Column(String)
    notes = Column(String, nullable=True)

class Orderbook(Base):
    __tablename__ = "orderbook"

    order_id = Column(String, primary_key=True, index=True)
    exchange_order_id = Column(String, nullable=True)
    status = Column(String)
    order_timestamp = Column(DateTime)
    exchange_timestamp = Column(DateTime, nullable=True)
    transaction_type = Column(String)
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

class AccountValue(Base):
    __tablename__ = "account_values"

    timestamp = Column(DateTime, primary_key=True, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)

class DailyAccountValue(Base):
    __tablename__ = "daily_account_values"

    date = Column(Date, primary_key=True, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)

class WeeklyAccountValue(Base):
    __tablename__ = "weekly_account_values"

    week_start_date = Column(Date, primary_key=True, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
