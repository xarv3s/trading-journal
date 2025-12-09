import pandas as pd
from datetime import datetime, date

# Mock Data
daily_ohlc = {
    date(2025, 12, 5): {'open': 100000, 'high': 105000, 'low': 99000, 'close': 102000}
}

# Mock Timeline DF
timeline_data = [
    {'date': datetime(2025, 11, 1), 'amount': 100000, 'type': 'TRANSACTION'}, # Initial Deposit
    # No other events, so account value stays constant until today?
    # Or maybe there are trades.
]
timeline_df = pd.DataFrame(timeline_data)

initial_capital = 0 # Since deposit is in timeline

# Logic from AnalyticsService.get_equity_curve
df = timeline_df.copy()
df['cumulative_change'] = df['amount'].cumsum()
df['account_value'] = initial_capital + df['cumulative_change']

# Resample
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
# Resample to daily. If we only have data on Nov 1, resample('D').last().ffill() will fill up to... when?
# It fills up to the last date in the index.
# If the last date in timeline is Nov 1, it won't generate a row for Dec 5!
daily_close = df['account_value'].resample('D').last().ffill()

print("Daily Close Index:")
print(daily_close.index)
print("\nLast Date:", daily_close.index[-1])

# Check if today is included
today = date(2025, 12, 5)
print(f"\nIs {today} in daily_close?", today in daily_close.index.date)

# Proposed Fix: Reindex to include today
if daily_close.index[-1].date() < today:
    print(f"\nExtending index to {today}")
    new_index = pd.date_range(start=daily_close.index[0], end=today, freq='D')
    daily_close = daily_close.reindex(new_index, method='ffill')
    
print("\nNew Last Date:", daily_close.index[-1])
print(f"Is {today} in daily_close now?", today in daily_close.index.date)
