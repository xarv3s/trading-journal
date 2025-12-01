import streamlit as st
import pandas as pd
from datetime import datetime
from repositories.trade_repository import TradeRepository

def render_capital_view(repository: TradeRepository):
    st.header("Capital Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add Transaction")
        with st.form("add_transaction_form"):
            date = st.date_input("Date", datetime.now())
            amount = st.number_input("Amount (₹)", min_value=0.0, step=1000.0)
            type = st.selectbox("Type", ["DEPOSIT", "WITHDRAWAL"])
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Transaction")
            if submitted:
                if amount > 0:
                    repository.add_transaction(date, amount, type, notes)
                    st.success(f"{type} of ₹{amount} added successfully!")
                    st.rerun()
                else:
                    st.error("Amount must be greater than 0.")
    
    with col2:
        st.subheader("Transaction History")
        transactions = repository.get_transactions()
        if transactions:
            df = pd.DataFrame([t.__dict__ for t in transactions])
            if '_sa_instance_state' in df.columns:
                df = df.drop(columns=['_sa_instance_state'])
            
            st.dataframe(
                df[['date', 'type', 'amount', 'notes']],
                column_config={
                    "date": st.column_config.DateColumn("Date", format="D MMM YYYY"),
                    "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No transactions found.")
