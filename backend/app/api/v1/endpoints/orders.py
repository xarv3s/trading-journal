from fastapi import APIRouter, HTTPException
from app.schemas import order as schemas
from app.services.kite_service import KiteClient
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

def get_kite_client():
    token = KiteClient.load_access_token()
    return KiteClient(api_key=settings.KITE_API_KEY, access_token=token)

@router.post("/place", response_model=schemas.OrderResponse)
def place_order(order: schemas.OrderPlace):
    kite = get_kite_client()
    if not kite.validate_token():
        raise HTTPException(status_code=401, detail="Kite session invalid")
    
    try:
        order_id = kite.place_order(
            tradingsymbol=order.tradingsymbol,
            exchange=order.exchange,
            transaction_type=order.transaction_type,
            quantity=order.quantity,
            price=order.price,
            product=order.product,
            order_type=order.order_type,
            variety=order.variety,
            trigger_price=order.trigger_price
        )
        return {"order_id": str(order_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
