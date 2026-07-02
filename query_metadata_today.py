from supabase import create_client
import os

supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_KEY'))
response = supabase.table('signals').select('*').limit(1).execute()
print(response.data)
