import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# 1. Fetch today's signals
url_fetch = f"{SUPABASE_URL}/rest/v1/signals?created_at=gte.2026-07-03T18:30:00Z"
req_fetch = urllib.request.Request(url_fetch, headers={
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
})

try:
    with urllib.request.urlopen(req_fetch) as response:
        signals = json.loads(response.read().decode())
        print(f"Found {len(signals)} signals from today to update.")
        
        # We will distribute different mock biases and day types among them
        biases = [
            "IN RANGE \n IN VALUE",
            "IN RANGE \n OUT OF VALUE",
            "OUT OF RANGE \n OUT OF VALUE"
        ]
        day_types = [
            "TYPICAL DAY, \n TRADING RANGE, \n SIDEWAYS",
            "BIG MOVE",
            "TREND DAY, \n DOUBLE DISTRIBUTION TREND, \n EXPANDED TYPICAL",
            "TREND DAY, \n DOUBLE DISTRIBUTION TREND",
            "TYPICAL DAY, \n EXPANDED TYPICAL DAY, \n TRADING RANGE"
        ]
        
        for idx, s in enumerate(signals):
            sig_id = s['id']
            # Cycle through mock combinations
            mock_bias = biases[idx % len(biases)]
            mock_day_type = day_types[idx % len(day_types)]
            
            # Preserve existing metadata if any
            existing_meta = s.get('metadata')
            if isinstance(existing_meta, str):
                try:
                    meta_obj = json.loads(existing_meta)
                except Exception:
                    meta_obj = {}
            elif isinstance(existing_meta, dict):
                meta_obj = existing_meta
            else:
                meta_obj = {}
                
            meta_obj['opening_bias'] = mock_bias
            meta_obj['day_type'] = mock_day_type
            
            # Perform update
            url_update = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{sig_id}"
            data_payload = json.dumps({"metadata": meta_obj}).encode('utf-8')
            req_update = urllib.request.Request(url_update, data=data_payload, headers=headers, method='PATCH')
            
            with urllib.request.urlopen(req_update) as upd_resp:
                pass
                
            print(f"Updated signal {sig_id} ({s['symbol']}) -> Bias: {mock_bias} | DayType: {mock_day_type}")
            
except Exception as e:
    print(f"Error: {e}")
