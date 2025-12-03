from fastapi import APIRouter
from app.api.v1.endpoints import login, trades, analytics, orders, market_data, transactions

api_router = APIRouter()
api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
