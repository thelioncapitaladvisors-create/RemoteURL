import re

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

# 1. Fix the container for MARKET WIDE PERFORMANCE
content = content.replace(
    '<div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 sm:gap-2.5">',
    '<div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5 shiny-card rounded-2xl p-2.5 border border-primary/20 bg-white/90 theme-gray:bg-slate-200/50 dark:bg-[#090e17]/95 shadow-lg backdrop-blur-xl mb-1 text-primary">'
)

# 2. Fix the wrappers inside MARKET WIDE PERFORMANCE
# We look for `<div className={...}>` or `<div className="...">` that have `wc-card-` or `hover:scale-[1.01]`
# Actually, it's easier to just regex replace the wrapper classes.
pattern_wrapper = re.compile(r'<div className="([^"]*?p-2 sm:p-2\.5 rounded-xl sm:rounded-2xl text-center min-w-0 overflow-hidden flex flex-col justify-between border transition-all duration-300[^"]*?wc-card-[^"]*?hover:scale-\[1\.01\][^"]*?)"')
content = pattern_wrapper.sub(r'<div className="p-1 text-center min-w-0 overflow-hidden flex flex-col justify-between">', content)

pattern_wrapper2 = re.compile(r'<div className=\{`([^`]*?p-2 sm:p-2\.5 rounded-xl sm:rounded-2xl text-center min-w-0 overflow-hidden flex flex-col justify-between border transition-all duration-300 hover:scale-\[1\.01\][^`]*?)`\}')
content = pattern_wrapper2.sub(r'<div className="p-1 text-center min-w-0 overflow-hidden flex flex-col justify-between">', content)

# 3. Fix the WIN / LOSS / B/E wrapper which is `col-span-1 sm:col-span-2 md:col-span-1 ...`
pattern_wrapper3 = re.compile(r'<div className="col-span-1 sm:col-span-2 md:col-span-1 p-2 sm:p-2\.5 rounded-xl sm:rounded-2xl text-center min-w-0 overflow-hidden flex flex-col justify-between border transition-all duration-300 wc-card-neutral hover:scale-\[1\.01\]">')
content = pattern_wrapper3.sub(r'<div className="p-1 text-center min-w-0 overflow-hidden flex flex-col justify-between">', content)

# 4. Fix the Equity Curve Row container inside MARKET WIDE PERFORMANCE
pattern_eq = re.compile(r'<div className="col-span-2 sm:col-span-3 md:col-span-4 p-3 sm:p-4 rounded-2xl border wc-card-neutral mt-2 flex items-center justify-between min-w-0 overflow-hidden">')
content = pattern_eq.sub(r'<div className="col-span-2 sm:col-span-4 border-t border-primary/10 pt-4 mt-2 flex items-center justify-between min-w-0 overflow-hidden">', content)


# 5. Fix the titles inside MARKET WIDE PERFORMANCE to just use `text-dim`
# e.g., `<div className="text-[8px] sm:text-[9px] md:text-[10px] leading-tight font-mono text-blue-700 theme-gray:text-blue-800 dark:text-blue-400 theme-lion:text-[#38bdf8] uppercase mb-1 font-black shrink-0">Total Trades</div>`
# regex for static strings:
pattern_title1 = re.compile(r'<div className="text-\[8px\] sm:text-\[9px\] md:text-\[10px\] leading-tight font-mono[^"]*?uppercase mb-1 font-black shrink-0">')
content = pattern_title1.sub(r'<div className="text-[8px] sm:text-[9px] md:text-[10px] leading-tight font-mono text-dim uppercase mb-1 font-black shrink-0">', content)

# regex for template literals: `<div className={`text-[8px] sm:text-[9px] md:text-[10px] leading-tight font-mono uppercase mb-1 font-black shrink-0 ${...}`}>Win Rate</div>`
pattern_title2 = re.compile(r'<div className=\{`text-\[8px\] sm:text-\[9px\] md:text-\[10px\] leading-tight font-mono uppercase mb-1 font-black shrink-0 \$\{([^}]*)\}`\}>')
content = pattern_title2.sub(r'<div className="text-[8px] sm:text-[9px] md:text-[10px] leading-tight font-mono text-dim uppercase mb-1 font-black shrink-0">', content)


# 6. NOW Fix the INDIVIDUAL MARKET STATS grids
# The wrapper is ALREADY `shiny-card rounded-2xl p-2.5 ...` in Individual Markets, we just need to fix the items inside it!
# It looks like: `<div className="flex flex-col items-center justify-center p-2 rounded-xl border wc-card-[color] transition-all duration-300 hover:scale-[1.02]">`
# Or template literal: `<div className={`flex flex-col items-center justify-center p-2 rounded-xl border transition-all duration-300 hover:scale-[1.02] ${...}`}>`

pattern_ind_wrap1 = re.compile(r'<div className="flex flex-col items-center justify-center p-2 rounded-xl border wc-card-[a-z]+ transition-all duration-300 hover:scale-\[1\.02\]">')
content = pattern_ind_wrap1.sub(r'<div className="flex flex-col items-center justify-center p-1 rounded-lg bg-primary/[0.03]">', content)

pattern_ind_wrap2 = re.compile(r'<div className=\{`flex flex-col items-center justify-center p-2 rounded-xl border transition-all duration-300 hover:scale-\[1\.02\] \$\{([^}]*)\}`\}>')
content = pattern_ind_wrap2.sub(r'<div className="flex flex-col items-center justify-center p-1 rounded-lg bg-primary/[0.03]">', content)

# And the titles in INDIVIDUAL MARKET STATS:
# `<span className="text-[7.5px] sm:text-[8px] uppercase tracking-widest text-blue-700 ... font-bold mb-0.5">`
pattern_ind_title1 = re.compile(r'<span className="text-\[7\.5px\] sm:text-\[8px\] uppercase tracking-widest[^"]*?font-bold mb-0\.5">')
content = pattern_ind_title1.sub(r'<span className="text-[7.5px] sm:text-[8px] uppercase tracking-widest text-dim font-bold mb-0.5">', content)

# `<span className={`text-[7.5px] sm:text-[8px] uppercase tracking-widest font-bold mb-0.5 ${...}`}>`
pattern_ind_title2 = re.compile(r'<span className=\{`text-\[7\.5px\] sm:text-\[8px\] uppercase tracking-widest font-bold mb-0\.5 \$\{([^}]*)\}`\}>')
content = pattern_ind_title2.sub(r'<span className="text-[7.5px] sm:text-[8px] uppercase tracking-widest text-dim font-bold mb-0.5">', content)


with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
