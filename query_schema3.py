import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("Tv-Alert-Mobile/.env.local")

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

try:
    res = supabase.table("signals").insert({
      "symbol": "TEST_EXTRA",
      "type": "LONG SCALP",
      "entry": 1.2500,
      "stop": 1.2400,
      "target": 1.2600,
      "status": "Active",
      "action": "buy",
      "opening_bias": "BULLISH"
    }).execute()
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
