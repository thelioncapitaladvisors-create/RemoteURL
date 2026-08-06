import os

filepath = '/Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx'
with open(filepath, 'r') as f:
    content = f.read()

# Extract the block to modify
start_idx = content.find('{/* ── TLCS DAY TYPE & SEQUENCE SCANNER ────────────────── */}')
end_idx = content.find('{/* ── AI MARKET INSIGHTS TAB ────────────────── */}', start_idx)

if start_idx != -1 and end_idx != -1:
    block = content[start_idx:end_idx]
    
    # Text replacements for light/dark mode compatibility
    replacements = {
        'text-amber-400 drop-shadow': 'text-amber-600 dark:text-amber-400 drop-shadow',
        'text-slate-300 font-mono': 'text-slate-500 dark:text-slate-300 font-mono',
        'border-b border-white/10 bg-black/40': 'border-b border-black/10 dark:border-white/10 bg-black/5 dark:bg-black/40',
        'text-emerald-400 border border-emerald-500/40 px-2.5 py-0.5 rounded-full bg-emerald-500/15': 'text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 dark:border-emerald-500/40 px-2.5 py-0.5 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15',
        'text-emerald-400 border border-emerald-500/40 px-2 py-0.5 rounded-full bg-emerald-500/15': 'text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 dark:border-emerald-500/40 px-2 py-0.5 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15',
        'bg-black/50 border-b border-amber-500/30 backdrop-blur-md': 'bg-black/10 dark:bg-black/50 border-b border-amber-500/30 backdrop-blur-md',
        'bg-amber-500/20 border border-amber-500/40 text-amber-400 font-black': 'bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/30 dark:border-amber-500/40 text-amber-600 dark:text-amber-400 font-black',
        'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 font-black': 'bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/30 dark:border-emerald-500/40 text-emerald-600 dark:text-emerald-400 font-black',
        'bg-rose-500/20 border border-rose-500/40 text-rose-400 font-black': 'bg-rose-500/10 dark:bg-rose-500/20 border border-rose-500/30 dark:border-rose-500/40 text-rose-600 dark:text-rose-400 font-black',
        "'bg-emerald-500/20 text-emerald-300 border border-emerald-500/45": "'bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 dark:border-emerald-500/45",
        "'bg-rose-500/20 text-rose-300 border border-rose-500/45": "'bg-rose-500/10 dark:bg-rose-500/20 text-rose-700 dark:text-rose-300 border border-rose-500/30 dark:border-rose-500/45",
        'border-b border-white/5 hover:bg-white/5': 'border-b border-black/5 dark:border-white/5 hover:bg-black/5 dark:hover:bg-white/5',
        'bg-black/40 border border-white/10 text-white font-extrabold': 'bg-black/10 dark:bg-black/40 border border-black/10 dark:border-white/10 text-slate-800 dark:text-white font-extrabold',
        'text-slate-400 text-xs italic': 'text-slate-500 dark:text-slate-400 text-xs italic',
        'bg-[#090e17]/95': 'bg-[#f8fafc]/90 dark:bg-[#090e17]/95',
    }
    
    for old, new in replacements.items():
        block = block.replace(old, new)
        
    content = content[:start_idx] + block + content[end_idx:]
    
    with open(filepath, 'w') as f:
        f.write(content)
