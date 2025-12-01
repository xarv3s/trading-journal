import streamlit as st
import plotly.express as px
from services.analytics_service import AnalyticsService

def render_analytics_view(analytics: AnalyticsService):
    st.header("Detailed Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Performance by Segment")
        segment_perf = analytics.get_performance_by_segment()
        if not segment_perf.empty:
            fig = px.bar(segment_perf, x='segment', y='net_pnl', title='PnL by Segment', color='net_pnl',
                         color_continuous_scale=['red', 'green'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for segment performance.")

    with col2:
        st.subheader("Performance by Setup")
        setup_perf = analytics.get_performance_by_setup()
        if not setup_perf.empty:
            fig = px.bar(setup_perf, x='setup_used', y='net_pnl', title='PnL by Setup', color='net_pnl',
                         color_continuous_scale=['red', 'green'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for setup performance.")
