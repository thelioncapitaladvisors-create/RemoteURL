import os
import time
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from dhanhq import dhanhq, DhanContext

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
PAPER_TRADING = os.getenv("PAPER_TRADING", "True").lower() == "true"

if not all([SUPABASE_URL, SUPABASE_KEY, DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN]):
    logger.error("Missing critical environment variables. Check your .env file.")
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Dhan HQ
try:
    dhan_context = DhanContext(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
    dhan = dhanhq(dhan_context)
    logger.info("Successfully connected to Dhan HQ.")
except Exception as e:
    logger.error(f"Failed to connect to Dhan HQ: {e}")
    exit(1)

# MCX Security ID Mapping (Example Mapping - Need actual IDs from Dhan's Security List)
# Users must update these with the correct current contract IDs
MCX_SYMBOLS = {
    "CRUDEOIL": {"security_id": "426307", "lot_size": 100},
    "GOLD": {"security_id": "426308", "lot_size": 1},
    "SILVER": {"security_id": "426309", "lot_size": 30},
    "NATURALGAS": {"security_id": "426310", "lot_size": 1250},
    "COPPER": {"security_id": "426311", "lot_size": 2500},
    "ZINC": {"security_id": "426312", "lot_size": 5000}
}

def clean_symbol(tv_symbol):
    """Normalize TradingView symbol to match our mapping"""
    sym = tv_symbol.upper()
    if sym.startswith('MCX:'): sym = sym.replace('MCX:', '')
    if sym.endswith('1!'): sym = sym.replace('1!', '')
    return sym

def place_dhan_order(signal):
    """Translates a TV signal into a Dhan HQ API call"""
    tv_symbol = signal.get("symbol", "")
    action = signal.get("action", "").upper()
    price = signal.get("price")
    
    symbol_clean = clean_symbol(tv_symbol)
    
    if symbol_clean not in MCX_SYMBOLS:
        logger.warning(f"Ignoring symbol {symbol_clean} - Not an active MCX mapped asset.")
        return

    mapping = MCX_SYMBOLS[symbol_clean]
    security_id = mapping["security_id"]
    quantity = mapping["lot_size"] # Configurable based on user preference

    transaction_type = dhan.BUY if action == "BUY" else dhan.SELL
    order_type = dhan.LIMIT if price else dhan.MARKET
    
    logger.info(f"Preparing order: {action} {quantity} x {symbol_clean} @ {price or 'MARKET'}")

    if PAPER_TRADING:
        logger.info(f"[PAPER TRADE] Would have executed: security_id={security_id}, transaction_type={transaction_type}, quantity={quantity}, price={price}")
        return

    try:
        response = dhan.place_order(
            security_id=security_id,
            exchange_segment=dhan.MCX,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            product_type=dhan.INTRA, # Or dhan.MARGIN
            price=float(price) if price else 0
        )
        logger.info(f"Order Placed! Response: {response}")
    except Exception as e:
        logger.error(f"Failed to place order: {e}")

def listen_for_signals():
    """Polls Supabase for new MCX signals created in the last few seconds"""
    logger.info("Starting Algo Engine. Listening for new TradingView webhooks...")
    last_checked_at = datetime.now(timezone.utc).isoformat()
    
    while True:
        try:
            # Query signals created after our last check
            response = supabase.table("tv_signals").select("*").gte("created_at", last_checked_at).execute()
            
            if response.data:
                for signal in response.data:
                    # Filter for MCX markets if needed (or let the mapping handle it)
                    place_dhan_order(signal)
                    
                # Update last checked timestamp to the latest signal's time
                last_checked_at = response.data[-1]["created_at"]
                
        except Exception as e:
            logger.error(f"Error querying Supabase: {e}")
            
        time.sleep(2) # Poll every 2 seconds

if __name__ == "__main__":
    listen_for_signals()
