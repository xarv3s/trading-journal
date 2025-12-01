import streamlit as st
import pandas as pd
from repositories.trade_repository import TradeRepository

def render_journal_view(repository: TradeRepository):
    st.header("Trade Log & Journal")

    trades = repository.get_unified_trades()
    if not trades:
        st.info("No trades found.")
        return

    # Convert to DataFrame for editing
    # trades is already a list of dicts
    df = pd.DataFrame(trades)
    
    # Columns to show/edit
    column_config = {
        "id": st.column_config.TextColumn(disabled=True), # Composite ID
        "trading_symbol": st.column_config.TextColumn(disabled=True),
        "entry_date": st.column_config.DatetimeColumn(disabled=True, format="D MMM YYYY, h:mm a"),
        "exit_date": st.column_config.DatetimeColumn(disabled=True, format="D MMM YYYY, h:mm a"),
        "pnl": st.column_config.NumberColumn(disabled=True, format="₹%.2f"),
        "setup_used": st.column_config.TextColumn("Setup Used"),
        "mistakes_made": st.column_config.TextColumn("Mistakes (Tags)"),
        "notes": st.column_config.TextColumn("Notes"),
        "is_mtf": st.column_config.CheckboxColumn("MTF?", default=False),
        "screenshot_path": st.column_config.TextColumn("Screenshot Path"),
    }
    
    visible_columns = ["id", "trading_symbol", "entry_date", "exit_date", "qty", "entry_price", "exit_price", "pnl", "setup_used", "mistakes_made", "notes", "is_mtf", "screenshot_path"]
    
    # Ensure all columns exist
    for col in visible_columns:
        if col not in df.columns:
            df[col] = None

    edited_df = st.data_editor(
        df[visible_columns],
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        key="trade_editor"
    )

    if st.button("Save Changes"):
        count = 0
        for index, row in edited_df.iterrows():
            # Find original row by ID
            original_row = df[df['id'] == row['id']].iloc[0]
            
            updates = {}
            if row['setup_used'] != original_row['setup_used']:
                updates['setup_used'] = row['setup_used']
            if row['mistakes_made'] != original_row['mistakes_made']:
                updates['mistakes_made'] = row['mistakes_made']
            if row['notes'] != original_row['notes']:
                updates['notes'] = row['notes']
            if row['is_mtf'] != original_row['is_mtf']:
                updates['is_mtf'] = 1 if row['is_mtf'] else 0
            if row['screenshot_path'] != original_row['screenshot_path']:
                updates['screenshot_path'] = row['screenshot_path']
            
            if updates:
                repository.update_trade(row['id'], updates)
                count += 1
        
        if count > 0:
            st.success(f"Updated {count} trades.")
            st.rerun()
        else:
            st.info("No changes detected.")
