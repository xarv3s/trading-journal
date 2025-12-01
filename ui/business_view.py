import streamlit as st
from services.analytics_service import AnalyticsService

def render_business_view(analytics: AnalyticsService):
    st.header("Business Overview (Quarterly Financials)")
    
    financials = analytics.get_quarterly_financials()
    if financials.empty:
        st.info("No data available.")
        return
        
    st.dataframe(
        financials,
        column_config={
            "quarter": "Quarter",
            "pnl": st.column_config.NumberColumn("Revenue (Gross PnL)", format="₹%.2f"),
            "estimated_charges": st.column_config.NumberColumn("COGS (Charges)", format="₹%.2f"),
            "mtf_interest": st.column_config.NumberColumn("Interest Expense", format="₹%.2f"),
            "net_pnl_after_charges": st.column_config.NumberColumn("Net Profit", format="₹%.2f"),
        },
        use_container_width=True,
        hide_index=True
    )
