import streamlit as st
import pandas as pd
from repositories.trade_repository import TradeRepository

def render_open_positions_view(repository: TradeRepository):
    st.header("Open Positions Management")
    
    trades = repository.get_unified_trades()
    open_trades = [t for t in trades if t['status'] == 'OPEN' or t['status'] == 'OPEN_Unrealized']
    
    if not open_trades:
        st.info("No open positions.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(open_trades)
    
    # Columns to show
    # We want to allow editing 'market_type'
    
    # Ensure strategy_type exists
    if 'strategy_type' not in df.columns:
        df['strategy_type'] = 'TRENDING'
        
    column_config = {
        "id": st.column_config.TextColumn(disabled=True),
        "trading_symbol": st.column_config.TextColumn("Symbol", disabled=True),
        "qty": st.column_config.NumberColumn("Qty", disabled=True),
        "entry_price": st.column_config.NumberColumn("Avg Price", disabled=True, format="₹%.2f"),
        "pnl": st.column_config.NumberColumn("Unrealized PnL", disabled=True, format="₹%.2f"),
        "strategy_type": st.column_config.SelectboxColumn(
            "Strategy Type",
            options=["TRENDING", "SIDEWAYS"],
            required=True
        ),
        "notes": st.column_config.TextColumn("Notes"),
        "is_mtf": st.column_config.CheckboxColumn("MTF?", default=False)
    }
    
    visible_columns = ["id", "trading_symbol", "qty", "entry_price", "pnl", "strategy_type", "notes", "is_mtf"]
    
    # Ensure columns exist
    for col in visible_columns:
        if col not in df.columns:
            df[col] = None
            
    edited_df = st.data_editor(
        df[visible_columns],
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        key="open_positions_editor"
    )
    
    if st.button("Save Changes"):
        count = 0
        for index, row in edited_df.iterrows():
            original_row = df[df['id'] == row['id']].iloc[0]
            
            updates = {}
            if row['strategy_type'] != original_row['strategy_type']:
                updates['strategy_type'] = row['strategy_type']
            if row['notes'] != original_row['notes']:
                updates['notes'] = row['notes']
            if row['is_mtf'] != original_row['is_mtf']:
                updates['is_mtf'] = 1 if row['is_mtf'] else 0
                
            if updates:
                repository.update_trade(row['id'], updates)
                count += 1
        
        if count > 0:
            st.success(f"Updated {count} trades.")
            st.rerun()
        else:
            st.info("No changes detected.")
