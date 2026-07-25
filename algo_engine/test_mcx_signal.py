import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

mock_signal = {
    "symbol": "MCX:CRUDEOIL1!",
    "type": "LONG SCALP",
    "entry": 6500.0,
    "status": "OPEN",
    "outcome": "OPEN",
    "metadata": '{"strategy": "algo_test"}'
}

try:
    logger.info("Inserting mock MCX signal to Supabase...")
    response = supabase.table("signals").insert(mock_signal).execute()
    logger.info(f"Insert successful: {response}")
except Exception as e:
    logger.error(f"Failed to insert signal: {e}")
