from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Order
from repositories.trade_repository import TradeRepository
import pandas as pd
from datetime import datetime

def test_save_orders():
    print("\n--- Testing Save Orders ---")
    # Setup in-memory DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    repo = TradeRepository(db)

    # Create dummy orders DataFrame
    orders_data = [{
        'order_id': '1001',
        'exchange_order_id': 'EX1001',
        'status': 'COMPLETE',
        'order_timestamp': datetime.now(),
        'exchange_timestamp': datetime.now(),
        'transaction_type': 'BUY',
        'tradingsymbol': 'INFY',
        'instrument_token': 123456,
        'product': 'CNC',
        'quantity': 10,
        'average_price': 1500.0,
        'filled_quantity': 10,
        'pending_quantity': 0,
        'cancelled_quantity': 0,
        'parent_order_id': None,
        'tag': 'test'
    }]
    df = pd.DataFrame(orders_data)

    # Test Save
    count = repo.save_orders(df)
    print(f"Saved count: {count}")
    assert count == 1
    
    # Verify in DB
    order = db.query(Order).filter(Order.order_id == '1001').first()
    assert order is not None
    assert order.tradingsymbol == 'INFY'
    
    # Test Update (Idempotency)
    orders_data[0]['status'] = 'OPEN' # Change something
    df_update = pd.DataFrame(orders_data)
    count_update = repo.save_orders(df_update)
    print(f"Update count: {count_update}")
    assert count_update == 0 # Should be 0 new records
    
    order_updated = db.query(Order).filter(Order.order_id == '1001').first()
    assert order_updated.status == 'OPEN'
    
    print("test_save_orders PASSED")

if __name__ == "__main__":
    test_save_orders()
