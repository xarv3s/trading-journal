from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any
from app.core.database import get_db
from app.repositories.trade_repository import TradeRepository
from app.schemas import trade as schemas
from app.services.kite_service import KiteClient
from app.services.cost_service import CostService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

def get_repository(db: Session = Depends(get_db)):
    return TradeRepository(db)

def get_kite_client():
    # In a real app, we'd handle token management better (e.g., from DB or Redis)
    # For now, we assume access_token is stored in a file or passed in headers (not implemented here)
    # We'll try to load from file
    token = KiteClient.load_access_token()
    return KiteClient(api_key=settings.KITE_API_KEY, access_token=token)

@router.get("/", response_model=schemas.PaginatedTrades)
def read_trades(
    skip: int = 0, 
    limit: int = 50, 
    sort_by: str = 'entry_date', 
    sort_desc: bool = True,
    status: str = None,
    repo: TradeRepository = Depends(get_repository)
):
    return repo.get_paginated_trades(skip=skip, limit=limit, sort_by=sort_by, sort_desc=sort_desc, status=status)

@router.patch("/{trade_id}", response_model=schemas.UnifiedTrade)
def update_trade(
    trade_id: str,
    updates: schemas.TradeUpdate,
    repo: TradeRepository = Depends(get_repository)
):
    # Convert Pydantic model to dict, excluding None values
    update_data = updates.model_dump(exclude_unset=True)
    trade = repo.update_trade(trade_id, update_data)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # We need to return a UnifiedTrade object. 
    # Since update_trade returns an ORM object (OpenTrade or ClosedTrade), we need to convert it.
    # Re-fetching the unified list is inefficient but safe. 
    # Better: Construct UnifiedTrade from the ORM object.
    
    # Helper to convert ORM to Unified dict (simplified version of get_unified_trades logic)
    t = trade
    is_open = hasattr(t, 'avg_price') # OpenTrade has avg_price, ClosedTrade has entry_price
    
    unified_dict = {
        'id': trade_id,
        'original_id': t.id,
        'source_table': 'OPEN' if is_open else 'CLOSED',
        'trading_symbol': t.symbol,
        'instrument_token': t.instrument_token,
        'exchange': t.exchange,
        'segment': 'EQ', # Default
        'order_type': t.product,
        'entry_date': t.entry_date,
        'exit_date': getattr(t, 'exit_date', None),
        'qty': t.qty,
        'entry_price': t.avg_price if is_open else t.entry_price,
        'exit_price': getattr(t, 'exit_price', None),
        'pnl': getattr(t, 'pnl', 0),
        'status': 'OPEN' if is_open else 'CLOSED',
        'is_mtf': t.is_mtf,
        'setup_used': t.setup_used,
        'mistakes_made': t.mistakes_made,
        'notes': t.notes,
        'screenshot_path': t.screenshot_path,
        'type': t.type,
        'strategy_type': t.strategy_type,
        'is_basket': getattr(t, 'is_basket', 0),
        'stop_loss': getattr(t, 'stop_loss', None)
    }
    return unified_dict

@router.get("/open", response_model=List[schemas.OpenTrade])
def read_open_trades(skip: int = 0, limit: int = 100, repo: TradeRepository = Depends(get_repository)):
    trades = repo.get_all_open_trades()
    return trades

@router.post("/sync")
def sync_trades(
    db: Session = Depends(get_db),
    repo: TradeRepository = Depends(get_repository)
):
    try:
        kite = get_kite_client()
        if not kite.validate_token():
            print("Token validation failed")
            raise HTTPException(status_code=401, detail="Kite session invalid")
        
        print("Fetching orders...")
        orders_df = kite.fetch_orders()
        print(f"Fetched {len(orders_df)} orders")
        
        # Filter out already processed orders
        existing_order_ids = repo.get_all_order_ids()
        new_orders_df = orders_df[~orders_df['order_id'].isin(existing_order_ids)].copy()
        
        print(f"Found {len(new_orders_df)} new orders to process")
        
        if new_orders_df.empty:
            return {"message": "Sync completed", "operations_count": 0, "new_orders": 0}
        
        open_trades = repo.get_all_open_trades()
        constituents = repo.get_basket_constituents()
        partial_closed_trades = repo.get_partial_closed_trades()
        
        print("Processing trades...")
        operations = kite.process_trades(new_orders_df, db_open_trades=open_trades, db_constituents=constituents, db_closed_trades=partial_closed_trades)
        print(f"Generated {len(operations)} operations")
        
        count = repo.apply_trade_operations(operations)
        print(f"Applied {count} operations")
        
        # Save processed orders to Orderbook
        print("Saving processed orders...")
        repo.save_orders(new_orders_df)
        
        # Cost Sync
        print("Updating costs...")
        cost_service = CostService(db)
        cost_service.update_daily_costs(orders_df)
        
        return {"message": "Sync completed", "operations_count": count}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Sync error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
