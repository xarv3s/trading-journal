from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1.api import api_router
from app.core.database import engine, Base

settings = get_settings()

# Create Tables (for now, usually use Alembic)
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Default for dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Trading Journal API is running"}

@app.on_event("startup")
async def startup_event():
    from app.services.instrument_service import InstrumentService
    from app.services.kite_service import KiteClient
    
    # Initialize Service (loads cache if exists)
    service = InstrumentService()
    
    # Try to sync if token exists
    try:
        token = KiteClient.load_access_token()
        if token:
            kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
            service.sync_instruments(kite)
    except Exception as e:
        print(f"Startup sync failed (non-critical): {e}")

    # Start Live Account Tracking
    import asyncio
    from app.services.live_account_service import LiveAccountService
    # Start background tasks
    asyncio.create_task(LiveAccountService().start_tracking())
    
    # Start Order Monitor
    from app.services.order_monitor_service import OrderMonitorService
    monitor = OrderMonitorService()
    asyncio.create_task(monitor.start_monitoring())
