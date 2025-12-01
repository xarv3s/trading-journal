import streamlit as st
import pandas as pd
from services.analytics_service import AnalyticsService

def render_insights_view(analytics: AnalyticsService):
    st.header("Trading Insights")
    
    insights = analytics.get_insights()
    if not insights:
        st.info("Not enough data for insights.")
        return
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Day of Week Performance")
        dow_data = pd.DataFrame(list(insights['dow_performance'].items()), columns=['Day', 'Avg PnL'])
        # Sort by day order if possible, or just display
        st.dataframe(dow_data, column_config={"Avg PnL": st.column_config.NumberColumn(format="₹%.2f")}, hide_index=True)
        
    with col2:
        st.subheader("Behavioral Metrics")
        st.metric("Holding Period vs PnL Correlation", f"{insights['holding_period_correlation']:.2f}")
        st.caption("Positive: Longer holding = More Profit. Negative: Quick exits = More Profit.")
