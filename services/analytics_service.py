import pandas as pd
import numpy as np
from database.models import Trade

class AnalyticsService:
    def __init__(self, trades: list):
        if not trades:
            self.df = pd.DataFrame()
        elif isinstance(trades[0], dict):
            self.df = pd.DataFrame(trades)
        else:
            self.df = pd.DataFrame([t.__dict__ for t in trades])
            
        if not self.df.empty:
            # Remove SQLAlchemy internal state if present
            if '_sa_instance_state' in self.df.columns:
                self.df = self.df.drop(columns=['_sa_instance_state'])
            
            self.df['entry_date'] = pd.to_datetime(self.df['entry_date'])
            self.df['exit_date'] = pd.to_datetime(self.df['exit_date'])
            
            # MTF Interest Calculation (Simplified: 18% per annum)
            # Interest = (Entry Price * Qty * 0.18 * Days Held) / 365
            # Only if is_mtf is True (1)
            self.df['days_held'] = (self.df['exit_date'] - self.df['entry_date']).dt.days
            self.df['days_held'] = self.df['days_held'].apply(lambda x: max(x, 1)) # Minimum 1 day
            
            def calculate_mtf_interest(row):
                if row.get('is_mtf', 0) == 1:
                    principal = row['entry_price'] * row['qty']
                    interest = (principal * 0.18 * row['days_held']) / 365
                    return interest
                return 0
            
            self.df['mtf_interest'] = self.df.apply(calculate_mtf_interest, axis=1)
            self.df['net_pnl'] = self.df['pnl'] - self.df['mtf_interest']
        else:
             # Initialize empty columns to avoid KeyErrors later
            self.df['net_pnl'] = []
            self.df['pnl'] = []
            self.df['segment'] = []
            self.df['setup_used'] = []
            self.df['exit_date'] = []
            
        self.timeline_df = pd.DataFrame()
        self.initial_capital = 0

    def get_kpis(self, strategy_type=None):
        df = self.df
        if strategy_type:
            if 'strategy_type' in df.columns:
                df = df[df['strategy_type'] == strategy_type]
            else:
                # If column missing, return empty or all? 
                # Better to return empty if filter requested but data missing
                return {
                    "total_pnl": 0, "win_rate": 0, "profit_factor": 0, 
                    "avg_rr": 0, "max_drawdown": 0, "total_trades": 0
                }

        if df.empty:
            return {
                "total_pnl": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "avg_rr": 0,
                "max_drawdown": 0,
                "total_trades": 0
            }

        total_pnl = df['net_pnl'].sum()
        winning_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(df)) * 100 if len(df) > 0 else 0
        
        gross_profit = winning_trades['net_pnl'].sum()
        gross_loss = abs(losing_trades['net_pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average Risk:Reward (Simplified approximation based on avg win / avg loss)
        avg_win = winning_trades['net_pnl'].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades['net_pnl'].mean()) if not losing_trades.empty else 0
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0

        # Max Drawdown
        cumulative_pnl = self.df.sort_values('exit_date')['net_pnl'].cumsum()
        peak = cumulative_pnl.cummax()
        drawdown = cumulative_pnl - peak
        max_drawdown = drawdown.min()

        return {
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_rr": avg_rr,
            "max_drawdown": max_drawdown,
            "total_trades": len(df)
        }



    def get_pnl_distribution(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df['net_pnl']

    def get_monthly_heatmap(self):
        if self.df.empty:
            return pd.DataFrame()
        
        daily_pnl = self.df.groupby(self.df['exit_date'].dt.date)['net_pnl'].sum().reset_index()
        daily_pnl.columns = ['date', 'pnl']
        return daily_pnl

    def get_performance_by_segment(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df.groupby('segment')['net_pnl'].sum().reset_index()

    def get_monthly_stats(self):
        if self.df.empty:
            return pd.DataFrame()
        
        # Ensure exit_date is datetime
        self.df['exit_date'] = pd.to_datetime(self.df['exit_date'])
        
        # Create Month-Year column for grouping
        self.df['month_year'] = self.df['exit_date'].dt.strftime('%Y-%m')
        
        stats = self.df.groupby('month_year').agg({
            'net_pnl': 'sum',
            'estimated_charges': 'sum',
            'id': 'count' # Count trades
        }).reset_index()
        
        stats = stats.rename(columns={'id': 'trades_count'})
        stats = stats.sort_values('month_year', ascending=False)
        
        return stats

    def calculate_costs(self, row):
        """
        Estimate Brokerage and Taxes (Zerodha rates approx).
        """
        segment = row['segment']
        turnover = (row['entry_price'] + row['exit_price']) * row['qty']
        
        brokerage = 0
        stt = 0
        exchange_txn = 0
        gst = 0
        sebi = 0
        stamp = 0
        
        if segment == 'EQ':
            # Delivery
            brokerage = 0
            stt = 0.001 * turnover # 0.1% on buy and sell
            exchange_txn = 0.0000345 * turnover # NSE
            sebi = 0.000001 * turnover
            stamp = 0.00015 * (row['entry_price'] * row['qty']) # 0.015% on buy
        elif segment == 'FUT':
            brokerage = min(40, 0.0003 * turnover) # 20 per order
            stt = 0.0001 * (row['exit_price'] * row['qty']) # 0.01% on sell
            exchange_txn = 0.00002 * turnover
            sebi = 0.000001 * turnover
            stamp = 0.00002 * (row['entry_price'] * row['qty'])
        elif segment == 'OPT':
            brokerage = 40 # 20 per order
            stt = 0.0005 * (row['exit_price'] * row['qty']) # 0.05% on sell premium
            exchange_txn = 0.00053 * turnover
            sebi = 0.000001 * turnover
            stamp = 0.00003 * (row['entry_price'] * row['qty'])
            
        gst = 0.18 * (brokerage + exchange_txn + sebi)
        
        total_charges = brokerage + stt + exchange_txn + gst + sebi + stamp
        return total_charges

    def enrich_data(self, initial_capital=100000, transactions=None):
        if self.df.empty:
            return

        self.df['estimated_charges'] = self.df.apply(self.calculate_costs, axis=1)
        self.df['net_pnl_after_charges'] = self.df['net_pnl'] - self.df['estimated_charges']
        
        # Calculate Account Value and Allocation
        # Sort by entry date to simulate account growth
        df_sorted = self.df.sort_values('entry_date')
        
        # Process Transactions
        transactions_df = pd.DataFrame()
        if transactions:
            # Explicitly convert to dict to ensure all attributes are loaded and keys exist
            data = []
            for t in transactions:
                data.append({
                    'date': t.date,
                    'amount': t.amount,
                    'type': t.type,
                    'notes': t.notes
                })
            transactions_df = pd.DataFrame(data)
            if not transactions_df.empty:
                if '_sa_instance_state' in transactions_df.columns:
                    transactions_df = transactions_df.drop(columns=['_sa_instance_state'])
                transactions_df['date'] = pd.to_datetime(transactions_df['date'])
                # Ensure amount is positive for deposit, negative for withdrawal based on type if needed, 
                # but let's assume the input is already signed or we handle it here.
                # Let's enforce sign based on type
                transactions_df['signed_amount'] = transactions_df.apply(
                    lambda x: abs(x['amount']) if x['type'] == 'DEPOSIT' else -abs(x['amount']), axis=1
                )

        # Create a combined timeline of PnL events and Transaction events
        pnl_events = []
        for _, row in self.df.iterrows():
            pnl_events.append({'date': row['exit_date'], 'amount': row['net_pnl_after_charges'], 'type': 'TRADE'})
            
        if not transactions_df.empty:
            for _, row in transactions_df.iterrows():
                pnl_events.append({'date': row['date'], 'amount': row['signed_amount'], 'type': 'TRANSACTION'})
            
        timeline_df = pd.DataFrame(pnl_events).sort_values('date')
        
        allocations = []
        account_values = []
        
        for _, row in df_sorted.iterrows():
            # Sum of PnL and Transactions realized before this trade entered
            realized_pnl = timeline_df[timeline_df['date'] < row['entry_date']]['amount'].sum()
            current_capital = initial_capital + realized_pnl
            
            trade_value = row['entry_price'] * row['qty']
            allocation = (trade_value / current_capital) * 100 if current_capital > 0 else 0
            
            allocations.append(allocation)
            account_values.append(current_capital)
            
        self.df['allocation_pct'] = allocations
        self.df['account_value_at_entry'] = account_values
        
        # Store timeline for equity curve
        self.timeline_df = timeline_df
        self.initial_capital = initial_capital

    def get_equity_curve(self):
        if not hasattr(self, 'timeline_df') or self.timeline_df.empty:
            if self.df.empty:
                return pd.DataFrame()
            # Fallback: Use Cumulative PnL as proxy for Account Value change
            df_sorted = self.df.sort_values('exit_date')
            df_sorted['cumulative_pnl'] = df_sorted['net_pnl'].cumsum()
            
            # Standardize columns to match expected output
            df_sorted = df_sorted.rename(columns={'exit_date': 'date', 'cumulative_pnl': 'account_value'})
            return df_sorted[['date', 'account_value']]
        
        # Calculate cumulative account value
        df = self.timeline_df.copy()
        df['cumulative_change'] = df['amount'].cumsum()
        df['account_value'] = self.initial_capital + df['cumulative_change']
        return df[['date', 'account_value']]

    def get_quarterly_financials(self):
        if self.df.empty:
            return pd.DataFrame()
        
        self.df['quarter'] = self.df['exit_date'].dt.to_period('Q')
        financials = self.df.groupby('quarter').agg({
            'pnl': 'sum', # Gross PnL (Revenue equivalent)
            'estimated_charges': 'sum', # Cost of Goods Sold / Expenses
            'mtf_interest': 'sum', # Interest Expense
            'net_pnl_after_charges': 'sum' # Net Profit
        }).reset_index()
        financials['quarter'] = financials['quarter'].astype(str)
        return financials

    def get_insights(self):
        if self.df.empty:
            return {}
            
        # Day of Week
        self.df['day_of_week'] = self.df['entry_date'].dt.day_name()
        dow_perf = self.df.groupby('day_of_week')['net_pnl_after_charges'].mean().to_dict()
        
        # Holding Period vs PnL
        holding_corr = self.df['days_held'].corr(self.df['net_pnl_after_charges'])
        
        return {
            "dow_performance": dow_perf,
            "holding_period_correlation": holding_corr
        }
    
    def get_trade_list(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df
