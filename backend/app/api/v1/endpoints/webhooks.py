from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from app.services.greeks_service import GreeksService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class BondYieldPayload(BaseModel):
    yield_value: float

@router.post("/tradingview/bond-yield")
def update_bond_yield(payload: BondYieldPayload = Body(...)):
    """
    Receive bond yield update from TradingView webhook.
    Payload: {"yield_value": 6.87}
    """
    try:
        # Validate range (sanity check)
        if not (0 < payload.yield_value < 20):
             raise HTTPException(status_code=400, detail="Invalid yield value. Must be between 0 and 20.")
             
        # Update service
        GreeksService.set_bond_yield(payload.yield_value)
        
        logger.info(f"Received bond yield update: {payload.yield_value}")
        return {"status": "success", "message": f"Bond yield updated to {payload.yield_value}"}
    except Exception as e:
        logger.error(f"Failed to update bond yield: {e}")
        raise HTTPException(status_code=500, detail=str(e))
