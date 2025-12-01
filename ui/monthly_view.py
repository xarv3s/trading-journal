import streamlit as st
import plotly.express as px
from services.analytics_service import AnalyticsService

def render_monthly_view(analytics: AnalyticsService):
    st.header("Monthly Performance")
    
    stats = analytics.get_monthly_stats()
    if stats.empty:
        st.info("No data available.")
        return
        
    st.dataframe(
        stats,
        column_config={
            "month_year": "Month",
            "net_pnl": st.column_config.NumberColumn("Net PnL", format="₹%.2f"),
            "trades_count": "Trades",
            "estimated_charges": st.column_config.NumberColumn("Charges", format="₹%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Chart
    fig = px.bar(stats, x='month_year', y='net_pnl', title='Monthly Net PnL', color='net_pnl',
                 color_continuous_scale=['red', 'green'])
    st.plotly_chart(fig, use_container_width=True)
