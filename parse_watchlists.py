import os
import re
import json

WATCHLIST_DIR = '/Users/vishant/Desktop/WATCHLISTS FOR SCANNER'
AGENTS_MD_PATH = '/Users/vishant/Documents/Project/.agents/AGENTS.md'

market_mapping = {
    'Watchlist_Nifty50.txt': 'nifty',
    'Watchlist_MCX.txt': 'mcx',
    'Watchlist_NYMEX.txt': 'nymex',
    'Watchlist_Crypto.txt': 'crypto',
    'Watchlist_Forex.txt': 'forex',
    'world_indices_watchlist.txt': 'world'
}

symbols_by_market = {}

for filename, market_key in market_mapping.items():
    filepath = os.path.join(WATCHLIST_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
            raw_symbols = re.split(r'[,\s\n\r]+', content)
            cleaned = set()
            for sym in raw_symbols:
                sym = sym.strip()
                if not sym:
                    continue
                clean_sym = sym.split(':')[-1]
                clean_sym = re.sub(r'1!$', '', clean_sym)
                clean_sym = clean_sym.strip()
                if clean_sym:
                    cleaned.add(clean_sym)
            symbols_by_market[market_key] = sorted(list(cleaned))

# Print the JSON representation
print(json.dumps(symbols_by_market, indent=2))

# 1. Update AGENTS.md
agents_update = "\n\n## Global Market Symbols Memory\n"
agents_update += "This is the definitive truth for symbol-to-market mappings. ALWAYS refer to these sets when categorizing markets or setting up filters.\n"
for market, syms in symbols_by_market.items():
    agents_update += f"- **{market}**: {', '.join(syms)}\n"

try:
    with open(AGENTS_MD_PATH, 'r') as f:
        agents_content = f.read()
    
    if "## Global Market Symbols Memory" in agents_content:
        agents_content = re.sub(r'## Global Market Symbols Memory.*', agents_update.strip(), agents_content, flags=re.DOTALL)
        with open(AGENTS_MD_PATH, 'w') as f:
            f.write(agents_content)
        print("Updated AGENTS.md with cleaned symbols.")
    else:
        with open(AGENTS_MD_PATH, 'a') as f:
            f.write(agents_update)
        print(f"Appended Market Symbols to {AGENTS_MD_PATH}")
except Exception as e:
    print(f"Could not update AGENTS.md: {e}")

# 2. Write a JS script to update Supabase
js_script = f"""
const {{ createClient }} = require('@supabase/supabase-js');
require('dotenv').config({{ path: '.env.local' }});

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {{
    console.error('Supabase URL or Key is missing.');
    process.exit(1);
}}

const supabase = createClient(supabaseUrl, supabaseKey);

const marketSymbols = {json.dumps(symbols_by_market, indent=2)};

async function syncToSupabase() {{
    console.log('Syncing market symbols to Supabase...');
    
    for (const [market_id, symbols] of Object.entries(marketSymbols)) {{
        const {{ error }} = await supabase
            .from('market_config')
            .upsert({{ market_id: market_id, symbols: symbols }}, {{ onConflict: 'market_id' }});
            
        if (error) {{
            console.error(`Error updating ${{market_id}}:`, error);
        }} else {{
            console.log(`Successfully synced ${{market_id}} with ${{symbols.length}} symbols.`);
        }}
    }}
}}

syncToSupabase();
"""
with open('sync_supabase.js', 'w') as f:
    f.write(js_script)

