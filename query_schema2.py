import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv("Tv-Alert-Mobile/.env.local")

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

res = supabase.table("signals").insert({
  "symbol": "GBPUSD",
  "type": "LONG SCALP",
  "entry": 1.2500,
  "stop": 1.2400,
  "target": 1.2600,
  "status": "Active",
  "pricing_type": "LIVE",
  "signal_ts": "2026-06-30T16:50:00Z"
}).execute()
print(res)
