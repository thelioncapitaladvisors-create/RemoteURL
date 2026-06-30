import urllib.request
import json
import os

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Fetch ALL closed signals
url = f"{SUPABASE_URL}/rest/v1/signals?select=id,symbol,type,status,outcome,r_multiple,entry,stop,exit_price,target&exit_price=not.is.null"

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"Fetched {len(data)} total closed signals.")
        
        fixed_count = 0
        for s in data:
            if not s.get('entry') or not s.get('stop') or not s.get('exit_price') or not s.get('type'):
                continue
                
            en = float(s['entry'])
            ep = float(s['exit_price'])
            sl = float(s['stop'])
            
            t = s['type'].upper()
            is_l = 'LONG' in t or 'BUY' in t
            is_s = 'SHORT' in t or 'SELL' in t
            
            if not is_l and not is_s:
                continue
                
            # Wait, if `stop` in DB is the trailing stop, the initial risk is wrong!
            # Let's see if we can calculate INITIAL risk from target!
            # If target exists, risk = abs(en - target) for 1R target? 
            # The user says "minimum 1:1" but they might use TP1, TP2 etc.
            # Usually Pine Script sends the initial STOP on entry, but overwrites it on trailing.
            # To just fix the SIGN, we only need to look at PROFIT.
            
            profit = (ep - en) if is_l else (en - ep)
            
            # If profit > 0, it's a WIN. If profit < 0, it's a LOSS.
            if profit > 0:
                true_outcome = 'WIN'
            elif profit < 0:
                true_outcome = 'LOSS'
            else:
                true_outcome = 'BREAKEVEN'
                
            db_r = s.get('r_multiple')
            db_outcome = s.get('outcome')
            
            needs_fix = False
            new_r = db_r
            
            if db_r is not None:
                db_r = float(db_r)
                if profit > 0 and db_r < 0:
                    # Inverted sign! Fix it by taking absolute value!
                    new_r = abs(db_r)
                    needs_fix = True
                elif profit < 0 and db_r > 0:
                    # Should be negative
                    new_r = -abs(db_r)
                    needs_fix = True
                    
            if db_outcome != true_outcome and true_outcome != 'BREAKEVEN':
                needs_fix = True
                
            # Strict text overrides
            st = (s.get('status') or '').upper()
            if 'TP' in st or 'TARGET' in st:
                true_outcome = 'WIN'
                if new_r is not None and new_r < 0:
                    new_r = abs(new_r)
                    needs_fix = True
                    
            if needs_fix:
                print(f"Fixing {s['symbol']} {s['type']}: DB_R={db_r} -> {new_r}, DB_OUTCOME={db_outcome} -> {true_outcome}")
                
                update_url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{s['id']}"
                update_data = json.dumps({
                    "r_multiple": new_r,
                    "outcome": true_outcome
                }).encode('utf-8')
                
                update_req = urllib.request.Request(update_url, data=update_data, headers=headers, method='PATCH')
                urllib.request.urlopen(update_req)
                fixed_count += 1
                
        print(f"Successfully fixed {fixed_count} corrupted signals.")
except Exception as e:
    print(f"Error: {e}")
