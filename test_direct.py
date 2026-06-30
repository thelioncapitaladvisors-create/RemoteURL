import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("Tv-Alert-Mobile/.env.local")

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

payload = {
    "symbol": "AUDUSD",
    "exchange": "FX_IDC",
    "type": "SELL",
    "entry": 0.68985,
    "stop": 0.68860,
    "trail_sl": 0.68860,
    "target": 0.68902,
    "status": "Active",
    "signal_ts": datetime.utcnow().isoformat()
}

res = supabase.table("signals").insert(payload).execute()
print(res)

if len(res.data) > 0:
    supabase.table("signals").delete().eq("id", res.data[0]["id"]).execute()
    print("Deleted")
