import asyncio
import logging
from typing import Dict, Optional
from app.services.kite_service import KiteClient
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

import pandas as pd
from app.core.database import SessionLocal
from app.repositories.trade_repository import TradeRepository

class OrderMonitorService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OrderMonitorService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.kite = KiteClient(api_key=settings.KITE_API_KEY)
        self._orders_cache: Dict[str, str] = {} # order_id -> status
        self._is_running = False
        self._initialized = True
        
    async def start_monitoring(self):
        """Starts the background monitoring loop."""
        if self._is_running:
            return
            
        self._is_running = True
        logger.info("Order Monitor Service started.")
        asyncio.create_task(self._monitoring_loop())
        
    async def stop_monitoring(self):
        """Stops the monitoring loop."""
        self._is_running = False
        logger.info("Order Monitor Service stopped.")
        
    async def _monitoring_loop(self):
        """Polls for order updates every 10 seconds."""
        while self._is_running:
            try:
                await self._check_orders()
            except Exception as e:
                logger.error(f"Error in order monitoring loop: {e}")
                
            await asyncio.sleep(10)
            
    async def _check_orders(self):
        """Fetches orders and checks for status changes."""
        try:
            # We need to ensure we have a valid session
            # KiteClient handles token loading, but we should check if it's ready
            if not self.kite.kite:
                # Try to reload token if possible or just skip
                token = self.kite.load_access_token()
                if token:
                    self.kite.kite.set_access_token(token)
                else:
                    # Not logged in yet
                    return

            orders = self.kite.get_orders()
            if not orders:
                return
                
            current_orders_map = {order['order_id']: order['status'] for order in orders}
            
            # Check for changes
            for order_id, status in current_orders_map.items():
                if order_id not in self._orders_cache:
                    # New order detected
                    logger.info(f"New Order Detected: ID={order_id}, Status={status}")
                    self._orders_cache[order_id] = status
                    
                    # If it's already COMPLETE (e.g. filled while we were down), sync it
                    if status == 'COMPLETE':
                        self._handle_order_update(order_id, status, orders)
                        
                else:
                    old_status = self._orders_cache[order_id]
                    if old_status != status:
                        # Status changed
                        logger.info(f"Order Status Changed: ID={order_id}, {old_status} -> {status}")
                        self._orders_cache[order_id] = status
                        
                        # Trigger sync if completed
                        if status == 'COMPLETE':
                            self._handle_order_update(order_id, status, orders)
                        
            # Update cache to remove stale orders if needed (optional, but good for memory)
            # For now, we keep them to avoid re-alerting if they reappear (unlikely for same day)
            
        except Exception as e:
            # Log debug to avoid spam if it's just a connection issue or auth issue
            logger.debug(f"Failed to fetch orders in monitor: {e}")

    def _handle_order_update(self, order_id: str, new_status: str, all_orders: list):
        """
        Callback for order updates.
        Syncs the order to DB if it is COMPLETE.
        """
        if new_status != 'COMPLETE':
            return

        try:
            # Find the full order object
            order = next((o for o in all_orders if o['order_id'] == order_id), None)
            if not order:
                return

            logger.info(f"Syncing completed order: {order_id}")
            
            # Create DataFrame for processing
            df = pd.DataFrame([order])
            
            # Process using TradeRepository
            with SessionLocal() as db:
                repo = TradeRepository(db)
                repo.process_orders(df)
                db.commit()
                
            logger.info(f"Successfully synced order: {order_id}")
            
        except Exception as e:
            logger.error(f"Failed to sync order {order_id}: {e}")
