import streamlit as st
import pandas as pd
from services.analytics_service import AnalyticsService

def render_trade_list_view(analytics: AnalyticsService):
    st.header("Detailed Trade List")
    
    df = analytics.get_trade_list()
    if df.empty:
        st.info("No trades found.")
        return

    # Format columns for display
    display_df = df.copy()
    
    # Select columns
    cols = [
        'trading_symbol', 'entry_date', 'exit_date', 'qty', 
        'entry_price', 'exit_price', 'pnl', 'estimated_charges', 
        'net_pnl_after_charges', 'days_held', 'allocation_pct', 
        'setup_used', 'mistakes_made'
    ]
    
    # Filter existing columns
    cols = [c for c in cols if c in display_df.columns]
    
    st.dataframe(
        display_df[cols],
        column_config={
            "entry_date": st.column_config.DatetimeColumn(format="D MMM YYYY"),
            "exit_date": st.column_config.DatetimeColumn(format="D MMM YYYY"),
            "pnl": st.column_config.NumberColumn("Gross PnL", format="₹%.2f"),
            "estimated_charges": st.column_config.NumberColumn("Charges", format="₹%.2f"),
            "net_pnl_after_charges": st.column_config.NumberColumn("Net PnL", format="₹%.2f"),
            "allocation_pct": st.column_config.ProgressColumn("Allocation %", min_value=0, max_value=100, format="%.2f%%"),
        },
        use_container_width=True,
        hide_index=True
    )
