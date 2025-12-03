import pandas as pd
from datetime import date
from app.models.all_models import DailyCost, OpenTrade
from sqlalchemy.orm import Session

class CostService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_brokerage(self, order):
        product = order.get('product')
        exchange = order.get('exchange')
        
        if product == 'CNC' and exchange in ['NSE', 'BSE']:
            return 0.0
        
        turnover = order['quantity'] * order['average_price']
        brokerage = min(20.0, turnover * 0.0003)
        return brokerage

    def calculate_taxes(self, order):
        turnover = order['quantity'] * order['average_price']
        exchange = order.get('exchange')
        txn_type = order.get('transaction_type')
        product = order.get('product')
        
        stt = 0.0
        if exchange in ['NSE', 'BSE']:
            if product == 'CNC':
                stt = turnover * 0.001
            else:
                if txn_type == 'SELL':
                    stt = turnover * 0.00025
        elif exchange == 'NFO':
            if txn_type == 'SELL':
                stt = turnover * 0.000125
        
        exch_txn = turnover * 0.0000345
        sebi = turnover * 0.000001
        
        stamp = 0.0
        if txn_type == 'BUY':
            if product == 'CNC':
                stamp = turnover * 0.00015
            else:
                stamp = turnover * 0.00003
                
        brokerage = self.calculate_brokerage(order)
        gst = (brokerage + exch_txn + sebi) * 0.18
        
        total_tax = stt + exch_txn + sebi + stamp + gst
        return total_tax

    def calculate_mtf_interest(self):
        mtf_trades = self.db.query(OpenTrade).filter(OpenTrade.product == 'MTF').all()
        total_mtf_value = sum(t.qty * t.avg_price for t in mtf_trades)
        interest = total_mtf_value * 0.0004
        return interest

    def update_daily_costs(self, orders_df, date_obj=None):
        if date_obj is None:
            date_obj = date.today()
            
        brokerage_total = 0.0
        taxes_total = 0.0
        
        if not orders_df.empty:
            orders_df['order_timestamp'] = pd.to_datetime(orders_df['order_timestamp'])
            daily_orders = orders_df[orders_df['order_timestamp'].dt.date == date_obj]
            
            for _, order in daily_orders.iterrows():
                order_dict = order.to_dict()
                brokerage_total += self.calculate_brokerage(order_dict)
                taxes_total += self.calculate_taxes(order_dict)
                
        mtf_interest = self.calculate_mtf_interest()
        total_cost = brokerage_total + taxes_total + mtf_interest
        
        daily_cost = self.db.query(DailyCost).filter(DailyCost.date == date_obj).first()
        if not daily_cost:
            daily_cost = DailyCost(date=date_obj)
            self.db.add(daily_cost)
            
        daily_cost.brokerage = brokerage_total
        daily_cost.taxes = taxes_total
        daily_cost.mtf_interest = mtf_interest
        daily_cost.total = total_cost
        
        self.db.commit()
        return daily_cost
