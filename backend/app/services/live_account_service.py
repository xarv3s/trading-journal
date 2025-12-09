
import asyncio
import logging
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.all_models import AccountValue, DailyEquity, Transaction, ClosedTrade, OpenTrade
from app.services.kite_service import KiteClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class LiveAccountService:
    _instance = None
    _running = False
    _current_candle = None
    _last_aggregation_time = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveAccountService, cls).__new__(cls)
        return cls._instance

    async def start_tracking(self):
        if self._running:
            return
        self._running = True
        logger.info("Starting Live Account Value Tracking...")
        asyncio.create_task(self._tracking_loop())

    async def _tracking_loop(self):
        while self._running:
            try:
                # 1. Check Market Status
                now = datetime.now()
                if not self._is_market_hours(now):
                    # logger.debug("Market closed.")
                    await asyncio.sleep(60)
                    continue

                # 2. Calculate Current Account Value
                value = self._calculate_account_value()
                if value is None:
                    logger.warning("Account value is None (Token missing or error).")
                    await asyncio.sleep(5)
                    continue
                
                logger.info(f"Calculated Account Value: {value}")

                # 3. Update Candle
                self._update_candle(now, value)

                # 4. Check for Aggregation (Every 5 minutes)
                if self._last_aggregation_time is None or (now - self._last_aggregation_time).total_seconds() > 300:
                    logger.info("Triggering scheduled aggregation...")
                    await self._run_aggregation()
                    self._last_aggregation_time = now

                # 5. Sleep
                await asyncio.sleep(5) # Sample every 5 seconds

            except Exception as e:
                logger.error(f"Error in live tracking loop: {e}")
                await asyncio.sleep(10)

    async def _run_aggregation(self):
        """
        Runs the batch aggregation process.
        """
        db = SessionLocal()
        try:
            from app.repositories.trade_repository import TradeRepository
            repo = TradeRepository(db)
            stats = repo.aggregate_account_values()
            logger.info(f"Scheduled Aggregation Completed: {stats}")
        except Exception as e:
            logger.error(f"Error in scheduled aggregation: {e}")
        finally:
            db.close()

    def _is_market_hours(self, dt):
        # Simple check: Mon-Fri, 9:15 - 15:30
        if dt.weekday() > 4: return False
        t = dt.time()
        start = datetime.strptime("09:15", "%H:%M").time()
        end = datetime.strptime("15:30", "%H:%M").time()
        return start <= t <= end

    def _calculate_account_value(self):
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # 1. Total Net Transactions (All Time)
            # Assuming Transaction.amount is positive and type determines sign
            total_deposits = db.query(func.sum(Transaction.amount)).filter(Transaction.type == 'DEPOSIT').scalar() or 0
            total_withdrawals = db.query(func.sum(Transaction.amount)).filter(Transaction.type == 'WITHDRAWAL').scalar() or 0
            net_transactions = total_deposits - total_withdrawals
            
            # 2. Total Realized PnL (All Time)
            total_realized = db.query(func.sum(ClosedTrade.pnl)).scalar() or 0
            
            # 3. Current Unrealized PnL (Live)
            open_trades = db.query(OpenTrade).all()
            total_unrealized = 0
            
            if open_trades:
                instruments = set()
                for t in open_trades:
                    if t.is_basket:
                        for c in t.constituents:
                            instruments.add(f"{c.exchange}:{c.symbol}")
                    else:
                        instruments.add(f"{t.exchange}:{t.symbol}")
                
                token = KiteClient.load_access_token()
                if token and instruments:
                    kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
                    ltp_map = kite.fetch_ltp(list(instruments))
                    
                    for t in open_trades:
                        if t.is_basket:
                            for c in t.constituents:
                                key = f"{c.exchange}:{c.symbol}"
                                ltp = ltp_map.get(key)
                                if ltp:
                                    pnl = (ltp - c.avg_price) * c.qty if c.type == 'LONG' else (c.avg_price - ltp) * c.qty
                                    total_unrealized += pnl
                        else:
                            key = f"{t.exchange}:{t.symbol}"
                            ltp = ltp_map.get(key)
                            if ltp:
                                pnl = (ltp - t.avg_price) * t.qty if t.type == 'LONG' else (t.avg_price - ltp) * t.qty
                                total_unrealized += pnl
                else:
                    if not token:
                        return None

            # Account Value = Net Transactions + Realized PnL + Unrealized PnL
            account_value = net_transactions + total_realized + total_unrealized
            return account_value

        except Exception as e:
            logger.error(f"Error calculating account value: {e}")
            return None
        finally:
            db.close()

    def _update_candle(self, now, value):
        # Round down to nearest minute
        minute_start = now.replace(second=0, microsecond=0)
        
        if self._current_candle and self._current_candle['timestamp'] == minute_start:
            # Update existing candle
            c = self._current_candle
            c['high'] = max(c['high'], value)
            c['low'] = min(c['low'], value)
            c['close'] = value
        else:
            # New minute started
            # 1. Save previous candle if exists
            if self._current_candle:
                self._save_candle(self._current_candle)
            
            # 2. Start new candle
            self._current_candle = {
                'timestamp': minute_start,
                'open': value,
                'high': value,
                'low': value,
                'close': value
            }

    def _save_candle(self, candle_data):
        db = SessionLocal()
        try:
            # Check if exists (idempotency)
            existing = db.query(AccountValue).filter(AccountValue.timestamp == candle_data['timestamp']).first()
            if existing:
                existing.high = max(existing.high, candle_data['high'])
                existing.low = min(existing.low, candle_data['low'])
                existing.close = candle_data['close']
                # Open usually doesn't change unless we missed the start
            else:
                candle = AccountValue(**candle_data)
                db.add(candle)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving candle: {e}")
        finally:
            db.close()
