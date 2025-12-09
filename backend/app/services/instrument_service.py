
import pandas as pd
import os
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

INSTRUMENTS_FILE = "instruments.csv"

class InstrumentService:
    _instance = None
    _lot_size_map = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InstrumentService, cls).__new__(cls)
            cls._instance.load_instruments()
        return cls._instance

    def load_instruments(self):
        """Load instruments from CSV into memory."""
        if os.path.exists(INSTRUMENTS_FILE):
            try:
                df = pd.read_csv(INSTRUMENTS_FILE)
                # Create a dictionary for fast lookup: symbol -> lot_size
                # We prioritize NFO/BFO segments for options/futures
                # But symbol names are usually unique within an exchange, but might overlap across exchanges (e.g. RELIANCE on NSE vs BSE)
                # However, for F&O, the trading symbol is unique (e.g. NIFTY25DECFUT).
                
                # Filter for relevant segments to keep memory usage low? 
                # No, let's keep all, 35k is small for memory.
                
                self._lot_size_map = dict(zip(df['tradingsymbol'], df['lot_size']))
                logger.info(f"Loaded {len(self._lot_size_map)} instruments into memory.")
            except Exception as e:
                logger.error(f"Error loading instruments cache: {e}")
        else:
            logger.warning("Instruments cache file not found. Lot sizes will fallback to defaults.")

    def sync_instruments(self, kite_client):
        """Fetch instruments from Kite and save to CSV."""
        try:
            logger.info("Syncing instruments from Zerodha...")
            df = kite_client.get_all_instruments(exchanges=['NSE', 'NFO', 'BSE', 'BFO', 'MCX'])
            if not df.empty:
                df.to_csv(INSTRUMENTS_FILE, index=False)
                logger.info(f"Saved {len(df)} instruments to {INSTRUMENTS_FILE}")
                self.load_instruments() # Reload into memory
                return True
            else:
                logger.warning("Fetched empty instruments dataframe.")
                return False
        except Exception as e:
            logger.error(f"Error syncing instruments: {e}")
            return False

    def get_lot_size(self, symbol):
        """Get lot size for a symbol. Returns None if not found."""
        return self._lot_size_map.get(symbol)
