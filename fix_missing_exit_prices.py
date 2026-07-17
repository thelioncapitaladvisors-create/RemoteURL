from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv('TLCS_Website_Deploy/.env.local')

url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)

response = supabase.table('signals').select('*').is_('exit_price', 'null').neq('status', 'Active').execute()
signals = response.data

updated = 0
for s in signals:
    exit_price = None
    outcome = (s.get('outcome') or '').upper()
    status = (s.get('status') or '').upper()
    
    if outcome == 'LOSS' or 'SL' in status or 'STOP' in status or 'LOSS' in status:
        exit_price = s.get('trail_sl') or s.get('stop')
    elif outcome == 'WIN' or 'TP' in status or 'TARGET' in status or 'WIN' in status:
        if 'TP4' in status and s.get('tp4'): exit_price = s.get('tp4')
        elif 'TP3' in status and s.get('tp3'): exit_price = s.get('tp3')
        elif 'TP2' in status and s.get('tp2'): exit_price = s.get('tp2')
        else: exit_price = s.get('target')
    elif outcome == 'BREAKEVEN' or 'B/E' in status:
        exit_price = s.get('entry')
        
    if exit_price is not None:
        try:
            supabase.table('signals').update({'exit_price': float(exit_price)}).eq('id', s['id']).execute()
            print(f"Updated ID {s['id']} ({s['symbol']}) with exit_price {exit_price}")
            updated += 1
        except Exception as e:
            print(f"Error updating {s['id']}: {e}")

print(f"Total updated: {updated}")
