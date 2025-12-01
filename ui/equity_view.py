import streamlit as st
import pandas as pd
import plotly.express as px
from repositories.trade_repository import TradeRepository

def render_equity_view(repository: TradeRepository):
    st.header("Equity Curve")
    
    try:
        history = repository.get_daily_equity_history()
        
        if not history:
            st.info("No equity history available yet. Sync trades to generate data.")
            return
            
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # --- Chart 1: Comparison (Rebased) ---
        st.subheader("Performance Comparison")
        
        # Rebase to 100
        if not df.empty:
            base_equity = df['account_value'].iloc[0]
            df['Equity (Rebased)'] = (df['account_value'] / base_equity) * 100
            
            # Indices
            for idx in ['nifty50', 'nifty_midcap150', 'nifty_smallcap250']:
                if idx in df.columns and df[idx].notna().any():
                    # Find first valid value
                    first_valid = df[idx].dropna().iloc[0]
                    df[f"{idx} (Rebased)"] = (df[idx] / first_valid) * 100
            
            # Plot
            cols_to_plot = ['Equity (Rebased)'] + [c for c in df.columns if 'Rebased' in c and c != 'Equity (Rebased)']
            fig_comp = px.line(df, x='date', y=cols_to_plot, title='Relative Performance (Base=100)', markers=True)
            fig_comp.update_layout(yaxis_title="Rebased Value")
            st.plotly_chart(fig_comp, use_container_width=True)
        
        st.divider()
        
        # --- Chart 2: Equity with EMAs ---
        st.subheader("Equity Curve with EMAs")
        
        # Calculate EMAs
        df['EMA 10'] = df['account_value'].ewm(span=10, adjust=False).mean()
        df['EMA 21'] = df['account_value'].ewm(span=21, adjust=False).mean()
        df['EMA 50'] = df['account_value'].ewm(span=50, adjust=False).mean()
        df['EMA 200'] = df['account_value'].ewm(span=200, adjust=False).mean()
        
        fig_ema = px.line(df, x='date', y=['account_value', 'EMA 10', 'EMA 21', 'EMA 50', 'EMA 200'], 
                          title='Equity Curve & EMAs', markers=True)
        fig_ema.update_layout(yaxis_title="Account Value")
        st.plotly_chart(fig_ema, use_container_width=True)
        
        # Stats
        if len(df) >= 2:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            change = latest['account_value'] - prev['account_value']
            pct_change = (change / prev['account_value']) * 100
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Equity", f"₹{latest['account_value']:,.2f}", f"{change:,.2f} ({pct_change:.2f}%)")
            col2.metric("Realized PnL", f"₹{latest['realized_pnl']:,.2f}")
            col3.metric("Unrealized PnL", f"₹{latest['unrealized_pnl']:,.2f}")
            
        # Data Table
        with st.expander("View Data"):
            st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
            
    except Exception as e:
        st.error(f"Error rendering equity view: {e}")
