from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.trade_repository import TradeRepository
from app.services.analytics_service import AnalyticsService

router = APIRouter()

def get_repository(db: Session = Depends(get_db)):
    return TradeRepository(db)

@router.get("/dashboard")
def get_dashboard_metrics(repo: TradeRepository = Depends(get_repository)):
    unified_trades = repo.get_unified_trades()
    analytics = AnalyticsService(unified_trades)
    analytics.enrich_data() # Add costs, etc.
    
    kpis = analytics.get_kpis()
    equity_curve = analytics.get_equity_curve().to_dict(orient='records')
    pnl_distribution = analytics.get_pnl_distribution()
    
    return {
        "kpis": kpis,
        "equity_curve": equity_curve,
        "pnl_distribution": pnl_distribution
    }
