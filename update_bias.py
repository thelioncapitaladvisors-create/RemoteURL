import urllib.request
import json
import ssl

url = "https://dwepduvhzuhzeehbeaaz.supabase.co/rest/v1"
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg",
    "Content-Type": "application/json"
}

context = ssl._create_unverified_context()

def get_pivots():
    req = urllib.request.Request(f"{url}/pivots", headers=headers)
    with urllib.request.urlopen(req, context=context) as response:
        return json.loads(response.read().decode())

def get_signals():
    req = urllib.request.Request(f"{url}/signals?select=id,symbol,metadata", headers=headers)
    with urllib.request.urlopen(req, context=context) as response:
        return json.loads(response.read().decode())

def update_signal(id, metadata):
    req = urllib.request.Request(f"{url}/signals?id=eq.{id}", data=json.dumps({"metadata": metadata}).encode(), headers={**headers, "Prefer": "return=minimal"}, method="PATCH")
    with urllib.request.urlopen(req, context=context) as response:
        pass

print("Fetching pivots...")
pivots = get_pivots()
pivot_map = {p['symbol']: p for p in pivots}

print("Fetching signals...")
signals = get_signals()

updated = 0
for sig in signals:
    sym = sig.get('symbol')
    meta = sig.get('metadata') or {}
    
    # If already has both, skip
    if meta.get('opening_bias') and meta.get('day_type'):
        continue
        
    p = pivot_map.get(sym)
    if not p:
        continue
        
    p_meta = p.get('metadata') or {}
    bias = p.get('opening_bias') or p_meta.get('opening_bias')
    day = p.get('day_type') or p_meta.get('day_type')
    zone = p.get('trade_zone') or p_meta.get('trade_zone')
    
    needs_update = False
    if bias and not meta.get('opening_bias'):
        meta['opening_bias'] = bias
        needs_update = True
    if day and not meta.get('day_type'):
        meta['day_type'] = day
        needs_update = True
    if zone and not meta.get('trade_zone'):
        meta['trade_zone'] = zone
        needs_update = True
        
    if needs_update:
        update_signal(sig['id'], meta)
        updated += 1
        if updated % 100 == 0:
            print(f"Updated {updated} signals...")

print(f"Done! Updated {updated} historical signals with Bias and Day Type.")
