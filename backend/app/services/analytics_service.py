import pandas as pd
import numpy as np

class AnalyticsService:
    def __init__(self, trades: list):
        if not trades:
            self.df = pd.DataFrame()
        elif isinstance(trades[0], dict):
            self.df = pd.DataFrame(trades)
        else:
            self.df = pd.DataFrame([t.__dict__ for t in trades])
            
        if not self.df.empty:
            if '_sa_instance_state' in self.df.columns:
                self.df = self.df.drop(columns=['_sa_instance_state'])
            
            self.df['entry_date'] = pd.to_datetime(self.df['entry_date'])
            self.df['exit_date'] = pd.to_datetime(self.df['exit_date'])
            
            self.df['days_held'] = (self.df['exit_date'] - self.df['entry_date']).dt.days
            self.df['days_held'] = self.df['days_held'].apply(lambda x: max(x, 1))
            
            def calculate_mtf_interest(row):
                if row.get('is_mtf', 0) == 1:
                    principal = row['entry_price'] * row['qty']
                    interest = (principal * 0.18 * row['days_held']) / 365
                    return interest
                return 0
            
            self.df['mtf_interest'] = self.df.apply(calculate_mtf_interest, axis=1)
            self.df['net_pnl'] = self.df['pnl'] - self.df['mtf_interest']
        else:
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
        
        # Win Rate: Calculated from CLOSED trades that are FULLY closed
        if 'closure_type' in df.columns:
            relevant_trades = df[(df['status'] == 'CLOSED') & (df['closure_type'] == 'FULL')]
        else:
            relevant_trades = df[df['status'] == 'CLOSED'] if 'status' in df.columns else df
            
        winning_relevant = relevant_trades[relevant_trades['net_pnl'] > 0]
        win_rate = (len(winning_relevant) / len(relevant_trades)) * 100 if not relevant_trades.empty else 0
        
        gross_profit = winning_trades['net_pnl'].sum()
        gross_loss = abs(losing_trades['net_pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        avg_win = winning_trades['net_pnl'].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades['net_pnl'].mean()) if not losing_trades.empty else 0
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0

        cumulative_pnl = self.df.sort_values('exit_date')['net_pnl'].cumsum()
        peak = cumulative_pnl.cummax()
        drawdown = cumulative_pnl - peak
        max_drawdown = drawdown.min()

        # Replace NaN with 0 or None for JSON serialization
        kpis = {
            "total_pnl": float(total_pnl),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor),
            "avg_rr": float(avg_rr),
            "max_drawdown": float(max_drawdown),
            "total_trades": int(len(df))
        }
        
        # Sanitize dictionary
        for k, v in kpis.items():
            if pd.isna(v) or np.isnan(v) or np.isinf(v):
                kpis[k] = 0.0
                
        return kpis
                
        return kpis

    def get_pnl_distribution(self):
        if self.df.empty:
            return []
            
        # Filter for closed trades
        if 'status' in self.df.columns:
            closed_trades = self.df[self.df['status'] == 'CLOSED'].copy()
        else:
            closed_trades = self.df.copy()
            
        if closed_trades.empty:
            return []
            
        def calculate_return_pct(row):
            invested = row['entry_price'] * row['qty']
            if invested == 0:
                return 0
            return (row['net_pnl'] / invested) * 100
            
        return closed_trades.apply(calculate_return_pct, axis=1).fillna(0).tolist()

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
        
        self.df['exit_date'] = pd.to_datetime(self.df['exit_date'])
        self.df['month_year'] = self.df['exit_date'].dt.strftime('%Y-%m')
        
        stats = self.df.groupby('month_year').agg({
            'net_pnl': 'sum',
            'estimated_charges': 'sum',
            'id': 'count'
        }).reset_index()
        
        stats = stats.rename(columns={'id': 'trades_count'})
        stats = stats.sort_values('month_year', ascending=False)
        return stats

    def calculate_costs(self, row):
        segment = row['segment']
        entry_price = row['entry_price']
        exit_price = row['exit_price']
        qty = row['qty']
        
        # Handle open trades where exit_price might be None
        if pd.isna(exit_price) or exit_price is None:
            exit_price = entry_price # Estimate using entry price
            
        turnover = (entry_price + exit_price) * qty
        
        brokerage = 0
        stt = 0
        exchange_txn = 0
        gst = 0
        sebi = 0
        stamp = 0
        
        if segment == 'EQ':
            brokerage = 0
            stt = 0.001 * turnover
            exchange_txn = 0.0000345 * turnover
            sebi = 0.000001 * turnover
            stamp = 0.00015 * (entry_price * qty)
        elif segment == 'FUT':
            brokerage = min(40, 0.0003 * turnover)
            stt = 0.0001 * (exit_price * qty)
            exchange_txn = 0.00002 * turnover
            sebi = 0.000001 * turnover
            stamp = 0.00002 * (entry_price * qty)
        elif segment == 'OPT':
            brokerage = 40
            stt = 0.0005 * (exit_price * qty)
            exchange_txn = 0.00053 * turnover
            sebi = 0.000001 * turnover
            stamp = 0.00003 * (entry_price * qty)
            
        gst = 0.18 * (brokerage + exchange_txn + sebi)
        total_charges = brokerage + stt + exchange_txn + gst + sebi + stamp
        return total_charges

    def enrich_data(self, initial_capital=0, transactions=None, daily_ohlc=None):
        if self.df.empty and (not transactions or len(transactions) == 0):
            return

        self.df['estimated_charges'] = self.df.apply(self.calculate_costs, axis=1)
        self.df['net_pnl_after_charges'] = self.df['net_pnl'] - self.df['estimated_charges']
        
        df_sorted = self.df.sort_values('entry_date')
        
        transactions_df = pd.DataFrame()
        if transactions:
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
                transactions_df['signed_amount'] = transactions_df.apply(
                    lambda x: abs(x['amount']) if x['type'] == 'DEPOSIT' else -abs(x['amount']), axis=1
                )

        pnl_events = []
        for _, row in self.df.iterrows():
            if pd.notna(row['exit_date']):
                pnl_events.append({'date': row['exit_date'], 'amount': row['net_pnl_after_charges'], 'type': 'TRADE'})
            
        if not transactions_df.empty:
            for _, row in transactions_df.iterrows():
                pnl_events.append({'date': row['date'], 'amount': row['signed_amount'], 'type': 'TRANSACTION'})
            
        if not pnl_events:
             timeline_df = pd.DataFrame(columns=['date', 'amount', 'type'])
        else:
            timeline_df = pd.DataFrame(pnl_events).sort_values('date')
        
        allocations = []
        account_values = []
        
        # Calculate allocations based on current capital at entry time
        # This is an approximation
        for _, row in df_sorted.iterrows():
            realized_pnl = timeline_df[timeline_df['date'] < row['entry_date']]['amount'].sum()
            current_capital = initial_capital + realized_pnl
            
            trade_value = row['entry_price'] * row['qty']
            allocation = (trade_value / current_capital) * 100 if current_capital > 0 else 0
            
            allocations.append(allocation)
            account_values.append(current_capital)
            
        self.df['allocation_pct'] = allocations
        self.df['account_value_at_entry'] = account_values
        
        self.timeline_df = timeline_df
        self.initial_capital = initial_capital
        self.daily_ohlc = daily_ohlc or {}

    def get_equity_curve(self, interval='D'):
        if not hasattr(self, 'timeline_df') or self.timeline_df.empty:
            if self.df.empty:
                return pd.DataFrame()
            # Fallback if no timeline (shouldn't happen with new logic but good for safety)
            df_sorted = self.df.sort_values('exit_date')
            df_sorted['cumulative_pnl'] = df_sorted['net_pnl'].cumsum()
            df_sorted = df_sorted.rename(columns={'exit_date': 'date', 'cumulative_pnl': 'account_value'})
            df_sorted = df_sorted.dropna(subset=['date'])
            return df_sorted[['date', 'account_value']]
        
        df = self.timeline_df.copy()
        df['cumulative_change'] = df['amount'].cumsum()
        df['account_value'] = self.initial_capital + df['cumulative_change']
        
        # Resample to daily to get closing value per day
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        daily_close = df['account_value'].resample('D').last().ffill()
        
        # Ensure we have a row for today, even if no events happened today
        today = pd.Timestamp.now().normalize()
        if not daily_close.empty and daily_close.index[-1] < today:
            new_index = pd.date_range(start=daily_close.index[0], end=today, freq='D')
            daily_close = daily_close.reindex(new_index, method='ffill')
            
        # Prepare Daily OHLC DataFrame
        daily_data = []
        for date, close_val in daily_close.items():
            date_obj = date.date()
            if date_obj < today.date():
                # Filter out history before today for Daily chart if interval is D
                # But for Weekly, we might want history? 
                # User said "Remove the data in the table prior to today" for the daily chart.
                # Assuming this applies to Weekly too for consistency, OR maybe weekly should show history?
                # "I also want a weekly chart here" implies showing history aggregated by week.
                # If we filter everything before today, weekly chart will just be one bar (this week).
                # Let's assume filtering applies to the *view*, so we generate full history here and filter in the loop based on interval?
                # Actually, the previous filter was hardcoded in the loop.
                pass

            if date_obj in self.daily_ohlc:
                ohlc = self.daily_ohlc[date_obj]
                daily_data.append({
                    'date': date,
                    'open': ohlc['open'],
                    'high': ohlc['high'],
                    'low': ohlc['low'],
                    'close': ohlc['close']
                })
            else:
                daily_data.append({
                    'date': date,
                    'open': close_val,
                    'high': close_val,
                    'low': close_val,
                    'close': close_val
                })
                
        df_daily = pd.DataFrame(daily_data).set_index('date')
        
        if interval == 'W':
            # Resample to Weekly
            # Rule: Open=first open, High=max high, Low=min low, Close=last close
            weekly = df_daily.resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last'
            })
            
            result_data = []
            for date, row in weekly.iterrows():
                # Filter out data prior to today as per user request
                # For weekly, we check if the week *ends* before today? 
                # Or if the week *contains* today?
                # The user wants "only data starting from today".
                # If today is Thursday, the weekly bar for this week ends on Sunday.
                # So we should include the current week.
                # Any week ending before today should be excluded?
                # Actually, let's be strict: if the week's data is entirely from before today, exclude it.
                # Since we resample to 'W' (Sunday), the date is the Sunday of that week.
                # If today is 2025-12-05 (Friday), the week ends 2025-12-07 (Sunday).
                # Previous week ended 2025-11-30.
                # So date >= today is too strict because the current week's date (Sunday) is in future.
                # But previous weeks are in past.
                # So we want to keep the week that *contains* today, and future weeks.
                # The week containing today ends on or after today.
                # But wait, `resample('W')` labels with the right edge (Sunday).
                # So `date` is the Sunday.
                # If `date` < today, then the week ended before today.
                # But we want to exclude "dashes with historical data".
                # If we have data for today, it falls into the current week.
                # So we just need to filter out weeks where the *end date* is before today?
                # Let's try that.
                
                # Wait, if we filter by `date < today`, we might exclude a week that ended yesterday but we want to see?
                # User said "I only want data starting from today".
                # So anything before today is "historical dashes".
                # So yes, filter out anything strictly before the current week.
                # The current week's label (Sunday) will be >= today (unless today is Sunday).
                # Actually, if today is Friday Dec 5, week ends Dec 7. Dec 7 >= Dec 5.
                # If today is Sunday Dec 7, week ends Dec 7. Dec 7 >= Dec 7.
                # So `date >= today` might work, but what if today is Monday and week ends Sunday?
                # Then `date` (next Sunday) > today.
                # What about previous week? Ends last Sunday. Last Sunday < today.
                # So `date < today` correctly filters out past weeks.
                
                # However, there's a catch: `today` variable is a Timestamp.
                # `date` is also Timestamp.
                # We need to compare dates.
                
                # Also, we need to ensure we don't filter out the *current* week if today is the start of it.
                # If today is Monday, week ends Sunday. Sunday > Monday. Kept.
                # If today is Sunday, week ends Sunday. Sunday == Sunday. Kept.
                # Seems correct.
                
                if date.date() < today.date():
                    continue

                result_data.append({
                    'date': date,
                    'account_value': row['close'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close']
                })
            df_result = pd.DataFrame(result_data)
            df_result = df_result.replace({np.nan: None})
            return df_result

        # Daily Interval
        result_data = []
        for date, row in df_daily.iterrows():
            date_obj = date.date()
            
            # Filter out data prior to today as per user request for Daily chart
            if interval == 'D' and date_obj < today.date():
                continue
                
            result_data.append({
                'date': date,
                'account_value': row['close'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })
                
        df_result = pd.DataFrame(result_data)
        df_result = df_result.replace({np.nan: None})
        return df_result

    def get_quarterly_financials(self):
        if self.df.empty:
            return pd.DataFrame()
        
        self.df['quarter'] = self.df['exit_date'].dt.to_period('Q')
        financials = self.df.groupby('quarter').agg({
            'pnl': 'sum',
            'estimated_charges': 'sum',
            'mtf_interest': 'sum',
            'net_pnl_after_charges': 'sum'
        }).reset_index()
        financials['quarter'] = financials['quarter'].astype(str)
        return financials

    def get_insights(self):
        if self.df.empty:
            return {}
            
        self.df['day_of_week'] = self.df['entry_date'].dt.day_name()
        dow_perf = self.df.groupby('day_of_week')['net_pnl_after_charges'].mean().to_dict()
        
        holding_corr = self.df['days_held'].corr(self.df['net_pnl_after_charges'])
        
        return {
            "dow_performance": dow_perf,
            "holding_period_correlation": holding_corr
        }
    
    def get_trade_list(self):
        if self.df.empty:
            return pd.DataFrame()
        return self.df
