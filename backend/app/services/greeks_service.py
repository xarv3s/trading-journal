
import math
from datetime import datetime, date
import re
import logging

logger = logging.getLogger(__name__)

# Standard Normal Cumulative Distribution Function
def norm_cdf(x):
    """Cumulative distribution function for the standard normal distribution."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

class GreeksService:
    def __init__(self):
        self.risk_free_rate = 0.10  # 10%
        self.default_iv = 0.15      # 15%

    import os
    _BOND_YIELD_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "market_data_cache.json")
    _BOND_YIELD_VAL = None
    _BOND_YIELD_TS = None

    def calculate_delta(self, S, K, T, r, sigma, option_type):
        """
        Calculate Delta using Black-Scholes model.
        S: Underlying Price
        K: Strike Price
        T: Time to Expiry (in years)
        r: Risk-free rate
        sigma: Volatility (IV)
        option_type: 'CE' or 'PE'
        """
        if T <= 0:
            # Expired or expiring today. 
            # If ITM, Delta = 1 (Call) or -1 (Put). If OTM, 0.
            if option_type == 'CE':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        
        if option_type == 'CE':
            return norm_cdf(d1)
        else:
            return norm_cdf(d1) - 1.0

    def parse_symbol(self, symbol):
        """
        Parse Zerodha trading symbol to extract metadata.
        Formats:
        1. Weekly: NIFTY23D0720900PE (SYMBOL YY M DD STRIKE TYPE)
           M: 1-9, O, N, D
        2. Monthly: NIFTY23DEC20900PE (SYMBOL YY MMM STRIKE TYPE)
        """
        # Regex for Weekly: (SYMBOL)(YY)(M)(DD)(STRIKE)(TYPE)
        # M is [1-9OND]
        weekly_pattern = r"^([A-Z]+)(\d{2})([1-9OND])(\d{2})(\d+)(CE|PE)$"
        
        # Regex for Monthly: (SYMBOL)(YY)(MMM)(STRIKE)(TYPE)
        monthly_pattern = r"^([A-Z]+)(\d{2})([A-Z]{3})(\d+)(CE|PE)$"
        
        # Try Weekly first
        match = re.match(weekly_pattern, symbol)
        if match:
            name, yy, m_char, dd, strike, otype = match.groups()
            year = 2000 + int(yy)
            day = int(dd)
            
            # Map M char to month
            m_map = {
                '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 
                '6': 6, '7': 7, '8': 8, '9': 9, 
                'O': 10, 'N': 11, 'D': 12
            }
            month = m_map.get(m_char)
            
            expiry = date(year, month, day)
            return {
                'underlying': name,
                'strike': float(strike),
                'type': otype,
                'expiry': expiry
            }
            
        # Try Monthly
        match = re.match(monthly_pattern, symbol)
        if match:
            name, yy, mmm, strike, otype = match.groups()
            year = 2000 + int(yy)
            
            # Map MMM to month (assuming standard English abbr)
            # Zerodha uses JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC
            mmm_map = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            month = mmm_map.get(mmm)
            
            # For monthly, it's usually the last Thursday. 
            # But we don't know the exact date from the symbol alone easily without calendar logic.
            # However, usually the symbol implies the expiry.
            # Wait, Monthly symbols DO NOT have the day. 
            # We need to find the last Thursday of that month.
            # This is a bit complex. 
            # Simplification: Use the 28th of the month as an approximation if exact date logic is too heavy?
            # Or implement Last Thursday logic.
            
            expiry = self.get_expiry_date(year, month)
            
            return {
                'underlying': name,
                'strike': float(strike),
                'type': otype,
                'expiry': expiry
            }
            
        return None

    def get_expiry_date(self, year, month):
        """Get the last Thursday of the month."""
        import calendar
        # Get last day of month
        last_day = calendar.monthrange(year, month)[1]
        dt = date(year, month, last_day)
        
        # Go back until Thursday (weekday 3)
        while dt.weekday() != 3:
            dt = dt.replace(day=dt.day - 1)
            
        # Check if it's a holiday? (Too complex for now, ignore holidays)
        return dt

    def get_underlying_symbol(self, name):
        """Map parsed name to Kite instrument symbol."""
        mapping = {
            'NIFTY': 'NSE:NIFTY 50',
            'BANKNIFTY': 'NSE:NIFTY BANK',
            'FINNIFTY': 'NSE:NIFTY FIN SERVICE',
            'MIDCPNIFTY': 'NSE:NIFTY MID SELECT',
            'SENSEX': 'BSE:SENSEX',
            'BANKEX': 'BSE:BANKEX'
        }
        return mapping.get(name)

    def calculate_iv(self, S, K, T, r, price, option_type):
        """
        Calculate Implied Volatility using py_vollib.
        """
        try:
            from py_vollib.black_scholes.implied_volatility import implied_volatility
            
            # py_vollib expects 'c' for Call and 'p' for Put
            flag = 'c' if option_type == 'CE' else 'p'
            
            # Handle edge cases
            if T <= 0: return 0
            if price <= 0: return 0
            
            iv = implied_volatility(price, S, K, T, r, flag)
            return iv
        except Exception as e:
            # logger.warning(f"IV calculation failed: {e}")
            return None

    def get_next_month_futures_symbol(self, underlying, today=None):
        """
        Generate the trading symbol for the next month's futures contract.
        Format: SYMBOLYYMMMFUT (e.g., NIFTY24JANFUT)
        """
        if not today:
            today = date.today()
            
        # Logic: If today is before expiry of current month, use next month?
        # User said "Next Month Expiry".
        # Let's assume we always look at the month *after* the current one to be safe/stable?
        # Or if we are early in the month, current month future is liquid.
        # "Next Month Expiry" usually means the one after the near month.
        # Let's target the month following the current month.
        
        year = today.year
        month = today.month
        
        # Next month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        # Zerodha Format: SYMBOL YY MMM FUT
        # YY is last 2 digits
        yy = str(next_year)[-2:]
        
        # MMM is JAN, FEB, etc.
        import calendar
        mmm = calendar.month_abbr[next_month].upper()
        
        # Symbol mapping (Underlying Name -> Futures Symbol Base)
        # Usually same, but NIFTY 50 -> NIFTY
        base_symbol = underlying
        if underlying == 'NIFTY 50': base_symbol = 'NIFTY'
        if underlying == 'NIFTY BANK': base_symbol = 'BANKNIFTY'
        if underlying == 'NIFTY FIN SERVICE': base_symbol = 'FINNIFTY'
        
        return f"{base_symbol}{yy}{mmm}FUT"

    @classmethod
    def set_bond_yield(cls, value):
        """
        Set the bond yield from an external source (e.g., TradingView Webhook).
        Persist to file.
        """
        import json
        import os
        
        cls._BOND_YIELD_VAL = value
        cls._BOND_YIELD_TS = datetime.now()
        
        try:
            data = {
                "bond_yield": value,
                "timestamp": cls._BOND_YIELD_TS.isoformat()
            }
            with open(cls._BOND_YIELD_CACHE_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to persist bond yield: {e}")

    def get_10y_bond_yield(self):
        """
        Fetch India 10Y Government Bond Yield.
        Priority:
        1. Webhook/Cache (if fresh < 24h)
        2. Synthetic Calculation (US 10Y + Spread)
        3. Fallback (7.2%)
        """
        # 1. Try Memory/File Cache
        if self._BOND_YIELD_VAL is None:
            # Try loading from file
            try:
                import json
                import os
                if os.path.exists(self._BOND_YIELD_CACHE_FILE):
                    with open(self._BOND_YIELD_CACHE_FILE, 'r') as f:
                        data = json.load(f)
                        self._BOND_YIELD_VAL = data.get('bond_yield')
                        self._BOND_YIELD_TS = datetime.fromisoformat(data.get('timestamp'))
            except Exception as e:
                logger.error(f"Failed to load bond yield cache: {e}")

        if self._BOND_YIELD_VAL is not None and self._BOND_YIELD_TS:
            # Check freshness (e.g., 24 hours)
            if (datetime.now() - self._BOND_YIELD_TS).total_seconds() < 86400:
                return self._BOND_YIELD_VAL / 100.0 if self._BOND_YIELD_VAL > 1 else self._BOND_YIELD_VAL

        # 2. Synthetic Calculation
        try:
            import yfinance as yf
            
            # Fetch US 10Y Treasury Yield
            ticker = yf.Ticker("^TNX") 
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                # ^TNX is in percent (e.g., 4.14)
                us_yield = hist['Close'].iloc[-1]
                
                # Add spread for India (approx 275 bps or 2.75%)
                india_yield_percent = us_yield + 2.75
                
                return india_yield_percent / 100.0
            
            # Fallback
            return 0.072

        except Exception as e:
            # logger.error(f"Failed to fetch bond yield: {e}")
            return 0.072

    def calculate_risk_free_rate(self, S, F, T):
        """
        Calculate risk-free rate using Cost of Carry model.
        r = (1/T) * ln(F/S)
        Clamped between 4% and 10%.
        """
        try:
            if T < 5/365.0: # Less than 5 days
                return 0.07 # Fallback to 7%
                
            if S <= 0 or F <= 0:
                return 0.07
                
            import numpy as np
            r = (1/T) * np.log(F/S)
            
            # Clamp
            r = max(0.04, min(r, 0.10))
            
            return r
        except Exception as e:
            # logger.error(f"Rate calculation failed: {e}")
            return 0.07

    def calculate_exposure(self, items, ltp_map):
        """
        Calculate delta-adjusted exposure for a list of items (trades/baskets).
        items: List of dicts with structure {type: 'BASKET'|'TRADE', constituents: [...]}
        ltp_map: Dict of {instrument_token: ltp} or {symbol: ltp}
        
        Returns: Dict {item_id: exposure}
        """
        results = {}
        today = date.today()
        
        for item in items:
            item_type = item.get('type')
            constituents = item.get('constituents', [])
            
            if item_type == 'BASKET':
                total_exposure = 0
                for c in constituents:
                    exp = self._calculate_single_exposure(c, ltp_map, today)
                    total_exposure += exp
                results[item['id']] = total_exposure
            
            elif item_type == 'TRADE':
                # Single Trade wrapped in item
                if constituents:
                    c = constituents[0]
                    exp = self._calculate_single_exposure(c, ltp_map, today)
                    results[item['id']] = exp
                else:
                    results[item['id']] = 0
            
            else:
                # Fallback for direct trade objects (if used elsewhere)
                exp = self._calculate_single_exposure(item, ltp_map, today)
                results[item.get('id')] = exp
                
        return results

    def _calculate_single_exposure(self, trade, ltp_map, today):
        # Handle different key names
        symbol = trade.get('tradingsymbol') or trade.get('trading_symbol') or trade.get('symbol')
        qty = trade.get('quantity') or trade.get('qty')
        exchange = trade.get('exchange')
        
        if not symbol or not qty:
            return 0
        
        # 1. Parse Symbol
        parsed = self.parse_symbol(symbol)
        
        if not parsed:
            # Fallback: Use Notional (LTP * Qty)
            key = f"{exchange}:{symbol}"
            ltp = ltp_map.get(key, 0)
            return ltp * qty

        # 2. Get Underlying LTP
        underlying_key = self.get_underlying_symbol(parsed['underlying'])
        S = ltp_map.get(underlying_key, 0)
        
        # Get Option LTP
        key = f"{exchange}:{symbol}"
        option_ltp = ltp_map.get(key, 0)
        
        if S == 0:
            # Fallback if underlying LTP not found
            return option_ltp * qty

        # 3. Calculate Risk-Free Rate
        # Fetch Futures Price
        fut_symbol = self.get_next_month_futures_symbol(parsed['underlying'], today)
        # Assuming Futures are on NFO exchange
        fut_key = f"NFO:{fut_symbol}"
        F = ltp_map.get(fut_key, 0)
        
        # Calculate Time to Futures Expiry (approx 30-60 days)
        # For simplicity, let's use the option's expiry T for the rate calculation if we don't have exact futures expiry
        # Or better, assume futures expiry is roughly 30 days from now if we can't calculate it easily
        # Actually, T in the formula is time to *futures* expiry.
        # We need the expiry date of the futures contract.
        # Parse the futures symbol to get expiry?
        # NIFTY24JANFUT -> Jan 2024. Expiry is last Thursday.
        # Let's reuse parse logic or get_expiry_date.
        
        # Quick parse of generated symbol
        # fut_symbol: NIFTY24JANFUT
        # We know the month and year from generation logic.
        # We can calculate expiry.
        
        # Re-derive year/month from today logic
        year = today.year
        month = today.month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        fut_expiry = self.get_expiry_date(next_year, next_month)
        T_fut = max((fut_expiry - today).days, 1) / 365.0
        
        r = self.calculate_risk_free_rate(S, F, T_fut)

        # 4. Calculate Delta
        K = parsed['strike']
        T_days = (parsed['expiry'] - today).days
        T = max(T_days, 0) / 365.0
        
        # If expiring today, T might be 0. Use small value
        if T == 0: T = 0.0001 
        
        # Calculate IV
        iv = self.calculate_iv(S, K, T, r, option_ltp, parsed['type'])
        
        # Use calculated IV or fallback to default
        sigma = iv if iv is not None else self.default_iv
        
        delta = self.calculate_delta(S, K, T, r, sigma, parsed['type'])
        
        # 5. Calculate Exposure
        # Exposure = |Delta * S * Qty|
        exposure = abs(delta * S * qty)
        
        return exposure

    def get_required_instruments(self, items):
        """
        Get list of instruments (symbols) required to calculate exposure.
        Includes the trade symbols, their underlyings, and Next Month Futures.
        """
        instruments = set()
        today = date.today()
        
        def process_trade(t):
            symbol = t.get('tradingsymbol') or t.get('trading_symbol') or t.get('symbol')
            exchange = t.get('exchange')
            if symbol and exchange:
                # Add the instrument itself
                instruments.add(f"{exchange}:{symbol}")
                
                # Check if we need underlying
                parsed = self.parse_symbol(symbol)
                if parsed:
                    underlying_name = parsed['underlying']
                    underlying = self.get_underlying_symbol(underlying_name)
                    if underlying:
                        instruments.add(underlying)
                        
                        # Add Next Month Futures
                        fut_symbol = self.get_next_month_futures_symbol(underlying_name, today)
                        instruments.add(f"NFO:{fut_symbol}")
        
        for item in items:
            item_type = item.get('type')
            constituents = item.get('constituents', [])
            
            if item_type == 'BASKET':
                for c in constituents:
                    process_trade(c)
            elif item_type == 'TRADE':
                for c in constituents:
                    process_trade(c)
            else:
                # Fallback
                process_trade(item)
                
        return list(instruments)
