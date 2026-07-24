import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

url = f"{SUPABASE_URL}/rest/v1/signals?select=*"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    signals = json.loads(response.read().decode())

def get_exact_pct(s):
    meta = s.get('metadata') or {}
    if isinstance(meta, str):
        try: meta = json.loads(meta)
        except: meta = {}
    return meta.get('exact_pct')

def resolve_outcome(s):
    st = (s.get('status') or '').upper()
    o = (s.get('outcome') or '').upper()
    if 'CANCEL' in o or 'CANCEL' in st or 'UNKNOWN' in st or 'UNKNOWN' in o: return 'CANCELLED'
    if ('EXPIRED' in st or 'COMPLETED' in st) and not s.get('exit_price'): return 'CANCELLED'
    meta = s.get('metadata') or {}
    if isinstance(meta, str):
        try: meta = json.loads(meta)
        except: meta = {}
    if meta.get('exact_pct') is not None:
        try:
            pct = float(meta['exact_pct'])
            if pct > 0: return 'WIN'
            if pct < 0: return 'LOSS'
            return 'BREAKEVEN'
        except: pass
    if 'ACTIVE' in st or o == 'OPEN' or st == 'OPEN': return 'OPEN'
    if o == 'WIN' or 'WIN' in st: return 'WIN'
    if o == 'LOSS' or 'LOSS' in st: return 'LOSS'
    if ('STOP' in st or 'SL' in st) and 'TRAIL' not in st: return 'LOSS'
    return 'OPEN'

closed = [s for s in signals if resolve_outcome(s) in ['WIN', 'LOSS', 'BREAKEVEN']]

wins = [s for s in closed if resolve_outcome(s) == 'WIN']
losses = [s for s in closed if resolve_outcome(s) == 'LOSS']

gross_profit = sum(abs(float(get_exact_pct(s))) for s in wins if get_exact_pct(s) is not None)
gross_loss = sum(abs(float(get_exact_pct(s))) for s in losses if get_exact_pct(s) is not None)

pf = gross_profit / gross_loss if gross_loss > 0 else 0

pcts = [float(get_exact_pct(s)) for s in closed if get_exact_pct(s) is not None]
avg_pct = sum(pcts) / len(pcts) if len(pcts) > 0 else 0

print(f"Total closed trades: {len(closed)}")
print(f"Wins: {len(wins)}, Losses: {len(losses)}")
print(f"Gross Profit: {gross_profit:.2f}%, Gross Loss: {gross_loss:.2f}%")
print(f"Overall Profit Factor (Gross Profit / Gross Loss): {pf:.2f}")
print(f"Average Profit % per trade (avg_pct): {avg_pct:.2f}%")
