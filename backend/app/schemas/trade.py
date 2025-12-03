from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

class TradeBase(BaseModel):
    symbol: str
    instrument_token: int
    qty: int
    exchange: str
    product: str
    strategy_type: Optional[str] = "TRENDING"
    notes: Optional[str] = None
    is_mtf: Optional[int] = 0
    is_basket: Optional[int] = 0
    stop_loss: Optional[float] = None

class OpenTradeCreate(TradeBase):
    avg_price: float
    entry_date: datetime
    type: str # LONG/SHORT
    max_exposure: int

class OpenTrade(OpenTradeCreate):
    id: int
    class Config:
        from_attributes = True

class ClosedTradeCreate(TradeBase):
    entry_price: float
    exit_price: float
    entry_date: datetime
    exit_date: datetime
    pnl: float
    type: str # LONG/SHORT
    closure_type: str # FULL/PARTIAL

class ClosedTrade(ClosedTradeCreate):
    id: int
    class Config:
        from_attributes = True

class DailyEquityBase(BaseModel):
    date: date
    account_value: float
    realized_pnl: float
    unrealized_pnl: float
    total_capital: float
    nifty50: Optional[float] = None
    nifty_midcap150: Optional[float] = None
    nifty_smallcap250: Optional[float] = None

class DailyEquity(DailyEquityBase):
    class Config:
        from_attributes = True

class TradeOperation(BaseModel):
    action: str
    data: Optional[dict] = None
    id: Optional[int] = None
    symbol: Optional[str] = None
    amount: Optional[float] = None
    cost_removed: Optional[float] = None
    pnl_realized: Optional[float] = None

class UnifiedTrade(BaseModel):
    id: str
    original_id: int
    source_table: str
    trading_symbol: str
    instrument_token: Optional[int]
    exchange: Optional[str]
    segment: Optional[str]
    order_type: Optional[str]
    entry_date: datetime
    exit_date: Optional[datetime]
    qty: int
    entry_price: float
    exit_price: Optional[float]
    pnl: float
    status: str
    is_mtf: Optional[int]
    setup_used: Optional[str]
    mistakes_made: Optional[str]
    notes: Optional[str]
    screenshot_path: Optional[str]
    type: str
    strategy_type: Optional[str]
    is_basket: Optional[int]
    stop_loss: Optional[float] = None

class TradeUpdate(BaseModel):
    notes: Optional[str] = None
    mistakes_made: Optional[str] = None
    setup_used: Optional[str] = None
    strategy_type: Optional[str] = None
    screenshot_path: Optional[str] = None
    stop_loss: Optional[float] = None

class PaginatedTrades(BaseModel):
    data: List[UnifiedTrade]
    total: int
    page: int
    page_size: int
