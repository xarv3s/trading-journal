from fastapi import APIRouter, HTTPException, Body
from app.services.kite_service import KiteClient
from app.core.config import get_settings
from typing import List, Dict

router = APIRouter()
settings = get_settings()

@router.post("/ltp")
def get_ltp(instruments: List[str] = Body(...)):
    """
    Fetch LTP for a list of instruments.
    """
    try:
        # In a real app, manage token better.
        token = KiteClient.load_access_token()
        if not token:
             raise HTTPException(status_code=401, detail="Not connected to Zerodha")
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        
        # Validate token if needed, but for speed maybe skip full validation if we trust the file?
        # kite.validate_token() # Optional, adds latency
        
        ltp_map = kite.fetch_ltp(instruments)
        return ltp_map
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_market_status():
    """
    Check if the market is open.
    """
    try:
        token = KiteClient.load_access_token()
        if not token:
             return {"open": False, "reason": "Not connected"}
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        is_open = kite.is_market_open()
        return {"open": is_open}
    except Exception as e:
        return {"open": False, "error": str(e)}

@router.post("/margins")
def get_margins(items: List[Dict] = Body(...)):
    """
    Fetch margins for a list of items.
    """
    try:
        token = KiteClient.load_access_token()
        if not token:
             # Return empty margins if not connected, or error?
             # Better to return error so UI knows
             raise HTTPException(status_code=401, detail="Not connected to Zerodha")
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        margins = kite.fetch_margins(items)
        return margins
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exposure")
def get_exposure(items: List[Dict] = Body(...)):
    """
    Calculate delta-adjusted exposure for a list of items.
    """
    try:
        from app.services.greeks_service import GreeksService
        greeks_service = GreeksService()
        
        token = KiteClient.load_access_token()
        if not token:
             raise HTTPException(status_code=401, detail="Not connected to Zerodha")
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        
        # 1. Get required instruments
        instruments = greeks_service.get_required_instruments(items)
        
        # 2. Fetch LTP
        ltp_map = kite.fetch_ltp(instruments)
        
        # 3. Calculate Exposure
        exposure = greeks_service.calculate_exposure(items, ltp_map)
        
        return exposure
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instruments/search")
def search_instruments(q: str, exchange: str = None):
    """
    Search for instruments.
    """
    try:
        token = KiteClient.load_access_token()
        if not token:
             raise HTTPException(status_code=401, detail="Not connected to Zerodha")
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        results = kite.search_instruments(q, exchange=exchange)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/option-chain/{symbol}")
def get_option_chain(symbol: str):
    """
    Fetch option chain for a given symbol (e.g., NIFTY, BANKNIFTY, INFY).
    Returns grouped data with Delta.
    """
    try:
        from app.services.greeks_service import GreeksService
        from datetime import date, datetime
        import pandas as pd
        
        token = KiteClient.load_access_token()
        if not token:
             raise HTTPException(status_code=401, detail="Not connected to Zerodha")
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        greeks_service = GreeksService()
        
        # 1. Fetch all NFO instruments (cached)
        df = kite.get_all_instruments(exchanges=['NFO'])
        if df.empty:
            return {"error": "No instruments found"}
            
        # 2. Filter by symbol
        # Symbol in NFO is usually "NIFTY", "BANKNIFTY", "INFY" in the 'name' column
        # Filter for OPTIDX (Index Options) or OPTSTK (Stock Options)
        mask = (df['name'] == symbol) & (df['segment'].isin(['NFO-OPT', 'NFO-FUT'])) # Include FUT for underlying price check? No, underlying is usually Index or Equity
        
        # Actually, for NIFTY/BANKNIFTY, underlying is in NSE index.
        # For Stocks, underlying is in NSE equity.
        
        chain_df = df[mask].copy()
        
        if chain_df.empty:
            return {"error": f"No options found for {symbol}"}
            
        # 3. Get Underlying Price
        # Map symbol to underlying key
        underlying_key = greeks_service.get_underlying_symbol(symbol)
        if not underlying_key:
            # Try guessing
            if symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                underlying_key = f"NSE:{symbol} 50" if symbol == 'NIFTY' else f"NSE:{symbol}"
                if symbol == 'BANKNIFTY': underlying_key = "NSE:NIFTY BANK"
                if symbol == 'FINNIFTY': underlying_key = "NSE:NIFTY FIN SERVICE"
            else:
                underlying_key = f"NSE:{symbol}"
        
        # Fetch Underlying LTP
        ltp_map = kite.fetch_ltp([underlying_key])
        underlying_ltp = ltp_map.get(underlying_key, 0)
        
        # 4. Prepare for Batch LTP Fetch of Options
        chain_df['expiry'] = pd.to_datetime(chain_df['expiry']).dt.date
        expiries = sorted(chain_df['expiry'].unique())
        
        # Let's try to do it for the nearest expiry (first one)
        nearest_expiry = expiries[0]
        
        # Filter for nearest expiry
        target_df = chain_df[chain_df['expiry'] == nearest_expiry]
        
        # Get tokens for LTP fetch
        instruments_to_fetch = [f"NFO:{row['tradingsymbol']}" for _, row in target_df.iterrows()]
        
        # Fetch LTPs
        opt_ltp_map = kite.fetch_ltp(instruments_to_fetch)
        
        # 5. Build Chain & Calculate Delta
        
        # Pre-calculate Risk Free Rate
        # Need Futures Price for RFR
        fut_symbol = greeks_service.get_next_month_futures_symbol(symbol)
        fut_key = f"NFO:{fut_symbol}"
        # Fetch future LTP too
        fut_ltp_map = kite.fetch_ltp([fut_key])
        F = fut_ltp_map.get(fut_key, 0)
        
        # Calculate RFR once
        T_fut = 30 / 365.0 
        r = greeks_service.calculate_risk_free_rate(underlying_ltp, F, T_fut)
        
        # Group by strike
        all_strikes = sorted(target_df['strike'].unique())
        
        # Filter for ATM +/- 10 strikes
        # Find ATM strike (closest to underlying_ltp)
        atm_strike = min(all_strikes, key=lambda x: abs(x - underlying_ltp))
        atm_index = all_strikes.index(atm_strike)
        
        start_index = max(0, atm_index - 20)
        end_index = min(len(all_strikes), atm_index + 21) # +21 because slice is exclusive
        
        strikes = all_strikes[start_index:end_index]
        
        strike_data = []
        
        today = date.today()
        
        for strike in strikes:
            strike_row = {'strike': strike}
            
            # Find CE and PE
            ce_row = target_df[(target_df['strike'] == strike) & (target_df['instrument_type'] == 'CE')]
            pe_row = target_df[(target_df['strike'] == strike) & (target_df['instrument_type'] == 'PE')]
            
            # Process CE
            if not ce_row.empty:
                ce = ce_row.iloc[0]
                key = f"NFO:{ce['tradingsymbol']}"
                ltp = opt_ltp_map.get(key, 0)
                
                # Calc Delta
                T = (nearest_expiry - today).days / 365.0
                if T <= 0: T = 0.0001
                
                # IV
                iv = greeks_service.calculate_iv(underlying_ltp, strike, T, r, ltp, 'CE')
                sigma = iv if iv else greeks_service.default_iv
                
                delta = greeks_service.calculate_delta(underlying_ltp, strike, T, r, sigma, 'CE')
                
                strike_row['ce'] = {
                    'symbol': ce['tradingsymbol'],
                    'ltp': ltp,
                    'delta': round(delta, 2),
                    'token': int(ce['instrument_token']),
                    'lot_size': int(ce['lot_size'])
                }
            
            # Process PE
            if not pe_row.empty:
                pe = pe_row.iloc[0]
                key = f"NFO:{pe['tradingsymbol']}"
                ltp = opt_ltp_map.get(key, 0)
                
                # Calc Delta
                T = (nearest_expiry - today).days / 365.0
                if T <= 0: T = 0.0001
                
                iv = greeks_service.calculate_iv(underlying_ltp, strike, T, r, ltp, 'PE')
                sigma = iv if iv else greeks_service.default_iv
                
                delta = greeks_service.calculate_delta(underlying_ltp, strike, T, r, sigma, 'PE')
                
                strike_row['pe'] = {
                    'symbol': pe['tradingsymbol'],
                    'ltp': ltp,
                    'delta': round(delta, 2),
                    'token': int(pe['instrument_token']),
                    'lot_size': int(pe['lot_size'])
                }
                
            strike_data.append(strike_row)
            
        return {
            "underlying": symbol,
            "underlying_ltp": underlying_ltp,
            "expiries": [d.isoformat() for d in expiries],
            "current_expiry": nearest_expiry.isoformat(),
            "chain": strike_data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
