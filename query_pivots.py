import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("Tv-Alert-Mobile/.env.local")

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

res = supabase.table("pivots").select("*").eq("symbol", "AUDUSD").execute()
print(res.data)
