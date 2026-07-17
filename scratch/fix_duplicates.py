import os
from supabase import create_client

supabase_url = os.environ.get("SUPABASE_URL", "https://qeqhvyvjohphtqpsixif.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_key:
    if os.path.exists(".env.local"):
        with open(".env.local") as f:
            for line in f:
                if line.startswith("NEXT_PUBLIC_SUPABASE_URL="):
                    supabase_url = line.strip().split("=")[1].strip('"\'')
                elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                    supabase_key = line.strip().split("=")[1].strip('"\'')

supabase = create_client(supabase_url, supabase_key)

# Get all signals from today
resp = supabase.table('signals').select('id, symbol, status, outcome, exit_price, trigger, created_at, entry, stop, type').order('created_at', desc=True).limit(2000).execute()
signals = resp.data

import datetime
today = datetime.datetime.utcnow().date()

# Group by symbol and entry price roughly
grouped = {}
for s in signals:
    key = f"{s['symbol']}_{round(s['entry'] if s['entry'] else 0, 2)}"
    if key not in grouped:
        grouped[key] = []
    grouped[key].append(s)

for key, group in grouped.items():
    if len(group) > 1:
        # Sort group by created_at so oldest is first
        group.sort(key=lambda x: x['created_at'])
        # Find the original (first) signal
        original = group[0]
        # Find any 'Hit SL' or 'Hit TP' that are later
        duplicates = group[1:]
        
        latest_status = original['status']
        for dup in duplicates:
            if dup['status'] in ['Hit SL', 'Hit TP', 'Closed', 'Stopped Out', 'Target Reached']:
                latest_status = dup['status']
                
        if latest_status != original['status']:
            print(f"Updating {original['symbol']} to {latest_status}")
            
            outcome = 'OPEN'
            if 'SL' in latest_status or 'Stop' in latest_status or 'Loss' in latest_status:
                outcome = 'LOSS'
            elif 'TP' in latest_status or 'Target' in latest_status or 'Win' in latest_status:
                outcome = 'WIN'
            
            exit_price = None
            if outcome == 'LOSS':
                exit_price = original['stop']
            elif outcome == 'WIN':
                # Target price?
                resp2 = supabase.table('signals').select('target').eq('id', original['id']).execute()
                if resp2.data:
                    exit_price = resp2.data[0]['target']
            
            exact_pct = None
            if exit_price and original['entry']:
                profit = (exit_price - original['entry']) if 'LONG' in original['type'] else (original['entry'] - exit_price)
                exact_pct = round((profit / original['entry']) * 100, 2)
                
            print(f"  New Outcome: {outcome}, Exit: {exit_price}, Pct: {exact_pct}")
            
            # Fetch existing metadata
            meta_resp = supabase.table('signals').select('metadata').eq('id', original['id']).execute()
            meta = meta_resp.data[0].get('metadata')
            import json
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    meta = {}
            if not meta:
                meta = {}
            
            meta['exact_pct'] = exact_pct
            
            supabase.table('signals').update({
                'status': latest_status,
                'outcome': outcome,
                'exit_price': exit_price,
                'metadata': meta
            }).eq('id', original['id']).execute()
            
            # Delete duplicates
            for dup in duplicates:
                print(f"  Deleting duplicate {dup['id']} ({dup['status']})")
                supabase.table('signals').delete().eq('id', dup['id']).execute()
