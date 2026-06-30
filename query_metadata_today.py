import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("Tv-Alert-Mobile/.env.local")

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
if not url or not key:
    print("Missing SUPABASE credentials")
    exit(1)

supabase: Client = create_client(url, key)

res = supabase.table("signals").select("*").order("created_at", desc=True).limit(5).execute()
print(json.dumps(res.data, indent=2))
