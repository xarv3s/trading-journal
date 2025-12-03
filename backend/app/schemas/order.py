from pydantic import BaseModel
from typing import Optional

class OrderPlace(BaseModel):
    tradingsymbol: str
    exchange: str
    transaction_type: str
    quantity: int
    price: Optional[float] = None
    product: str
    order_type: str
    variety: Optional[str] = "regular"
    trigger_price: Optional[float] = None

class OrderResponse(BaseModel):
    order_id: str
