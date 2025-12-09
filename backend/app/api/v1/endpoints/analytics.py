from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.trade_repository import TradeRepository
from app.services.analytics_service import AnalyticsService

router = APIRouter()

def get_repository(db: Session = Depends(get_db)):
    return TradeRepository(db)

@router.get("/dashboard")
def get_dashboard_metrics(interval: str = 'D', repo: TradeRepository = Depends(get_repository)):
    unified_trades = repo.get_unified_trades()
    transactions = repo.get_transactions()
    daily_ohlc = repo.get_daily_ohlc_from_candles()
    analytics = AnalyticsService(unified_trades)
    analytics.enrich_data(transactions=transactions, daily_ohlc=daily_ohlc) # Add costs, etc.
    
    kpis = analytics.get_kpis()
    equity_curve = analytics.get_equity_curve(interval=interval).to_dict(orient='records')
    pnl_distribution = analytics.get_pnl_distribution()
    
    return {
        "kpis": kpis,
        "equity_curve": equity_curve,
        "pnl_distribution": pnl_distribution
    }

@router.get("/intraday-equity")
def get_intraday_equity(db: Session = Depends(get_db)):
    from app.models.all_models import AccountValue
    candles = db.query(AccountValue).order_by(AccountValue.timestamp.asc()).all()
    return candles

@router.post("/aggregate")
def trigger_aggregation(repo: TradeRepository = Depends(get_repository)):
    """
    Triggers the Lambda Architecture batch aggregation.
    Aggregates AccountValue -> DailyAccountValue & WeeklyAccountValue.
    """
    result = repo.aggregate_account_values()
    return {"message": "Aggregation completed", "stats": result}

@router.get("/daily-equity")
def get_daily_equity(db: Session = Depends(get_db)):
    from app.models.all_models import DailyAccountValue
    data = db.query(DailyAccountValue).order_by(DailyAccountValue.date.asc()).all()
    return data

@router.get("/weekly-equity")
def get_weekly_equity(db: Session = Depends(get_db)):
    from app.models.all_models import WeeklyAccountValue
    data = db.query(WeeklyAccountValue).order_by(WeeklyAccountValue.week_start_date.asc()).all()
    return data
