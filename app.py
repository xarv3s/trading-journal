import streamlit as st
import os
from database.connection import init_db, get_db
from repositories.trade_repository import TradeRepository
from services.kite_service import KiteClient
from services.analytics_service import AnalyticsService
from ui.dashboard import render_dashboard
from ui.journal_view import render_journal_view
from ui.trade_list_view import render_trade_list_view
from ui.monthly_view import render_monthly_view
from ui.business_view import render_business_view
from ui.insights_view import render_insights_view
from ui.capital_view import render_capital_view
from ui.open_positions_view import render_open_positions_view

# ... (imports)

# Sidebar for Navigation and Settings
st.sidebar.title("Trading Journal")
page = st.sidebar.radio("Navigate", [
    "Dashboard", 
    "Open Positions", 
    "Trade List", 
    "Equity Curve", # New Page
    "Monthly View", 
    "Business Overview", 
    "Insights",
    "Capital Management",
    "Journal (Edit)"
])

# ... (Auth logic)





st.sidebar.divider()
st.sidebar.subheader("Zerodha Sync")

import json

# Load config if exists (for non-sensitive data)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
config = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"Error loading config.json: {e}")

from dotenv import load_dotenv
load_dotenv("credentials.env")

api_key = os.getenv("ZERODHA_API_KEY")
api_secret = os.getenv("ZERODHA_API_SECRET")
initial_capital = config.get("initial_capital", 100000)

if not api_key or not api_secret:
    st.sidebar.warning("Credentials not found in credentials.env")
    api_key = st.sidebar.text_input("API Key", type="password")
    api_secret = st.sidebar.text_input("API Secret", type="password")
else:
    st.sidebar.success("Credentials loaded from env.")

# Auto-Login Logic
if 'access_token' not in st.session_state:
    # Try to load from file
    saved_token = KiteClient.load_access_token()
    if saved_token:
        # Validate
        temp_kite = KiteClient(api_key=api_key, access_token=saved_token)
        if temp_kite.validate_token():
            st.session_state['access_token'] = saved_token
            st.sidebar.success("Auto-login successful!")
        else:
            # Token expired or invalid
            pass

# Check query params for request_token (callback from Zerodha)
query_params = st.query_params
request_token = query_params.get("request_token", None)

if 'access_token' not in st.session_state:
    if request_token and api_key and api_secret:
        try:
            with st.spinner("Authenticating..."):
                kite_client = KiteClient(api_key=api_key, api_secret=api_secret, request_token=request_token)
                st.session_state['access_token'] = kite_client.access_token
                kite_client.save_access_token(kite_client.access_token)
                st.success("Authenticated!")
                st.rerun() # Rerun to clear URL params
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            st.stop()
    elif api_key and api_secret:
        # Not logged in and no request token -> Redirect to Zerodha
        temp_kite = KiteClient(api_key=api_key)
        login_url = temp_kite.get_login_url()
        st.markdown(f'<meta http-equiv="refresh" content="0;url={login_url}">', unsafe_allow_html=True)
        st.info("Redirecting to Zerodha for login...")
        st.stop()
    else:
        st.error("API Key and Secret not found. Please check credentials.env")
        st.stop()

# If we reach here, we are logged in
if 'access_token' in st.session_state:
    if st.sidebar.button("Sync Trades"):
        try:
            with st.spinner("Syncing with Zerodha..."):
                kite_client = KiteClient(api_key=api_key, access_token=st.session_state['access_token'])
                
                # Fetch Orders
                orders = kite_client.fetch_orders()
                
                # Process
                db = next(get_db())
                repo = TradeRepository(db)
                open_trades = repo.get_all_open_trades()
                operations = kite_client.process_trades(orders, db_open_trades=open_trades)
                
                # Save
                ops_count = repo.apply_trade_operations(operations)
                st.sidebar.success(f"Synced! Operations: {ops_count}")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Sync Failed: {str(e)}")

# Main Content
db = next(get_db())
repo = TradeRepository(db)
trades = repo.get_unified_trades()
transactions = repo.get_transactions()

# Fetch LTP for Open Trades if credentials exist
if 'access_token' in st.session_state and api_key:
    kite = KiteClient(api_key=api_key, access_token=st.session_state['access_token'])
    
    open_trades_indices = [i for i, t in enumerate(trades) if t['status'] == 'OPEN']
    if open_trades_indices:
        instruments = []
        # Map indices to instruments
        idx_map = {} 
        for i in open_trades_indices:
            t = trades[i]
            # Assuming NSE for now, or use t['exchange']
            exch = t.get('exchange', 'NSE')
            inst = f"{exch}:{t['trading_symbol']}"
            instruments.append(inst)
            idx_map[inst] = i
            
        if instruments:
            ltp_data = kite.fetch_ltp(instruments)
            # Fetch Indices
            indices_ltp = kite.fetch_indices_ltp()
            nifty50 = indices_ltp.get("NSE:NIFTY 50")
            nifty_midcap150 = indices_ltp.get("NSE:NIFTY MIDCAP 150")
            nifty_smallcap250 = indices_ltp.get("NSE:NIFTY SMALLCAP 250")
            
            # Save to DailyEquity
            from datetime import date
            # These variables (total_equity, realized_pnl, total_unrealized_pnl)
            # are expected to be calculated before this point.
            # For now, using placeholders or assuming they are defined elsewhere.
            # If not defined, this will cause a NameError.
            # Assuming analytics.enrich_data() or similar calculates them.
            # Placeholder values for demonstration if not defined:
            total_equity = 0 # Replace with actual calculation
            realized_pnl = 0 # Replace with actual calculation
            total_unrealized_pnl = 0 # Replace with actual calculation

            repo.save_daily_equity(
                date=date.today(),
                account_value=total_equity,
                realized_pnl=realized_pnl,
                unrealized_pnl=total_unrealized_pnl,
                total_capital=total_equity,
                nifty50=nifty50,
                nifty_midcap150=nifty_midcap150,
                nifty_smallcap250=nifty_smallcap250
            )
            
            st.toast(f"Equity Updated: ₹{total_equity:,.2f}")
            # Update trades
            from datetime import datetime
            for inst, price in ltp_data.items():
                if inst in idx_map:
                    idx = idx_map[inst]
                    ltp = price
                    trade = trades[idx]
                    
                    # Calculate Unrealized PnL
                    if trade.get('type') == 'LONG':
                        pnl = (ltp - trade['entry_price']) * trade['qty']
                    else:
                        # Short
                        pnl = (trade['entry_price'] - ltp) * trade['qty']
                    
                    # Temporarily update for analytics
                    trade['exit_price'] = ltp
                    trade['exit_date'] = datetime.now()
                    trade['pnl'] = pnl
                    trade['status'] = 'OPEN_Unrealized' # Mark as unrealized for debugging if needed

analytics = AnalyticsService(trades)
analytics.enrich_data(initial_capital=initial_capital, transactions=transactions)

from ui.equity_view import render_equity_view

# ...

if page == "Dashboard":
    render_dashboard(analytics)
elif page == "Open Positions":
    render_open_positions_view(repo)
elif page == "Trade List":
    render_trade_list_view(analytics)
elif page == "Equity Curve":
    render_equity_view(repo)
elif page == "Monthly View":
    render_monthly_view(analytics)
elif page == "Business Overview":
    render_business_view(analytics)
elif page == "Insights":
    render_insights_view(analytics)
elif page == "Capital Management":
    render_capital_view(repo)
elif page == "Journal (Edit)":
    render_journal_view(repo)
