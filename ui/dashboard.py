import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from services.analytics_service import AnalyticsService

def render_dashboard(analytics: AnalyticsService):
    st.header("Dashboard")
    
    try:
        # Overall Stats
        st.subheader("Overall Performance")
        kpis_overall = analytics.get_kpis()
        render_kpi_row(kpis_overall)
        
        st.divider()
        
        # Segregated Stats
        col_trend, col_side = st.columns(2)
        
        with col_trend:
            st.subheader("Trending Markets")
            kpis_trend = analytics.get_kpis(strategy_type='TRENDING')
            render_kpi_card(kpis_trend)
            
        with col_side:
            st.subheader("Sideways Markets")
            kpis_side = analytics.get_kpis(strategy_type='SIDEWAYS')
            render_kpi_card(kpis_side)

            kpis_side = analytics.get_kpis(strategy_type='SIDEWAYS')
            render_kpi_card(kpis_side)

    except Exception as e:
        st.error(f"Error rendering dashboard: {str(e)}")
        st.exception(e)

def render_kpi_row(kpis):
    # Row 1: Key Financials
    col1, col2, col3 = st.columns(3)
    col1.metric("Total P&L", f"₹{kpis['total_pnl']:,.2f}")
    col2.metric("Max Drawdown", f"₹{kpis['max_drawdown']:,.2f}")
    col3.metric("Win Rate", f"{kpis['win_rate']:.2f}%")
    
    # Row 2: Ratios & Stats
    col4, col5, col6 = st.columns(3)
    col4.metric("Profit Factor", f"{kpis['profit_factor']:.2f}")
    col5.metric("Avg R:R", f"{kpis['avg_rr']:.2f}")
    col6.metric("Total Trades", f"{kpis['total_trades']}")

def render_kpi_card(kpis):
    st.metric("Total P&L", f"₹{kpis['total_pnl']:,.2f}")
    st.metric("Win Rate", f"{kpis['win_rate']:.2f}%")
    st.metric("Profit Factor", f"{kpis['profit_factor']:.2f}")
    st.metric("Total Trades", f"{kpis['total_trades']}")
