from fastapi import APIRouter, HTTPException, Body
from app.services.kite_service import KiteClient
from app.core.config import get_settings
from typing import List, Dict

router = APIRouter()
settings = get_settings()

@router.post("/ltp")
def get_ltp(instruments: List[str] = Body(...)):
    """
    Fetch LTP for a list of instruments.
    """
    try:
        # In a real app, manage token better.
        token = KiteClient.load_access_token()
        if not token:
             raise HTTPException(status_code=401, detail="Not connected to Zerodha")
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        
        # Validate token if needed, but for speed maybe skip full validation if we trust the file?
        # kite.validate_token() # Optional, adds latency
        
        ltp_map = kite.fetch_ltp(instruments)
        return ltp_map
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_market_status():
    """
    Check if the market is open.
    """
    try:
        token = KiteClient.load_access_token()
        if not token:
             return {"open": False, "reason": "Not connected"}
             
        kite = KiteClient(api_key=settings.KITE_API_KEY, access_token=token)
        is_open = kite.is_market_open()
        return {"open": is_open}
    except Exception as e:
        return {"open": False, "error": str(e)}
