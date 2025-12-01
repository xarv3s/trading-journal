from datetime import date
from repositories.trade_repository import TradeRepository
from database.models import DailyEquity
from database.connection import SessionLocal

def test_daily_equity_persistence():
    print("\n--- Testing Daily Equity Persistence ---")
    
    session = SessionLocal()
    repo = TradeRepository(session)
    
    # 1. Test Save (Insert)
    today = date.today()
    repo.save_daily_equity(
        today, 100000, 5000, 2000, 107000,
        nifty50=19500.5, nifty_midcap150=12000.0, nifty_smallcap250=9000.0
    )
    
    history = repo.get_daily_equity_history()
    assert len(history) > 0
    latest = history[-1]
    assert latest['date'] == today
    assert latest['account_value'] == 100000
    assert latest['nifty50'] == 19500.5
    assert latest['nifty_midcap150'] == 12000.0
    
    print("Insert Passed!")
    
    # 2. Test Update
    repo.save_daily_equity(
        today, 110000, 6000, 3000, 119000,
        nifty50=19600.0
    )
    
    history = repo.get_daily_equity_history()
    latest = history[-1]
    assert latest['account_value'] == 110000
    assert latest['nifty50'] == 19600.0
    # Ensure others didn't get wiped if not passed (logic check)
    # My logic: if nifty50 is not None: entry.nifty50 = nifty50
    # So if I pass None, it should stay same? 
    # Wait, my logic was:
    # if nifty50 is not None: entry.nifty50 = nifty50
    # So if I don't pass it (default None), it persists.
    # But here I am only passing nifty50.
    assert latest['nifty_midcap150'] == 12000.0 # Should persist
    
    print("Update Passed!")
    
    # Cleanup (Optional, but good for repeatable tests)
    # session = SessionLocal()
    # session.query(DailyEquity).filter_by(date=today).delete()
    # session.commit()
    # session.close()

if __name__ == "__main__":
    test_daily_equity_persistence()
