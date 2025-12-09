import sys
import os
import yfinance as yf
from datetime import date

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.greeks_service import GreeksService

def calculate_basket():
    service = GreeksService()
    
    # 1. Fetch NIFTY Spot
    print("Fetching NIFTY 50 Spot Price...")
    try:
        ticker = yf.Ticker("^NSEI")
        hist = ticker.history(period="1d")
        if not hist.empty:
            S = hist['Close'].iloc[-1]
            print(f"Spot Price (S): {S:.2f}")
        else:
            print("Failed to fetch Spot. Using fallback 24600.")
            S = 24600.0
    except Exception as e:
        print(f"Error fetching spot: {e}")
        S = 24600.0

    # 2. Define Basket
    # Qty = 75 for all
    qty = 75
    symbols = [
        "NIFTY25D0925700PE",
        "NIFTY25D0926250CE",
        "NIFTY26DEC28000PE",
        "NIFTY26MAR25000CE",
        "NIFTY26MAR25000PE"
    ]
    
    print("\nCalculating Exposure...")
    print(f"{'Symbol':<20} {'Type':<5} {'Strike':<8} {'Expiry':<12} {'Delta':<8} {'Exposure':<12}")
    print("-" * 70)
    
    total_exposure = 0
    
    for sym in symbols:
        parsed = service.parse_symbol(sym)
        if not parsed:
            print(f"Failed to parse {sym}")
            continue
            
        K = parsed['strike']
        expiry = parsed['expiry']
        otype = parsed['type']
        
        # Calculate T
        today = date.today()
        T_days = (expiry - today).days
        T = max(T_days, 0) / 365.0
        if T == 0: T = 0.0001
        
        # Calculate Delta
        # Using r=0.07 (approx) and sigma=0.15 (default) since we don't have option prices
        # Ideally we'd use the dynamic rate, but let's stick to a reasonable baseline for estimation
        r = 0.07 
        sigma = 0.15
        
        delta = service.calculate_delta(S, K, T, r, sigma, otype)
        
        # Exposure
        exp = abs(delta * S * qty)
        total_exposure += exp
        
        print(f"{sym:<20} {otype:<5} {K:<8} {expiry}   {delta:.4f}   {exp:,.2f}")
        
    print("-" * 70)
    print(f"Total Gross Exposure: ₹{total_exposure:,.2f}")

if __name__ == "__main__":
    calculate_basket()
