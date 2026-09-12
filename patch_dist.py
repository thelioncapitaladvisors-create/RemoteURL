import re

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

# 1. Update the Timeframe Selector
old_tf = """<div className="flex items-center bg-secondary/40 p-0.5 rounded-lg border border-primary/15 overflow-x-auto hide-scrollbar">
                                  {(['TODAY', 'WEEK', 'MONTH', 'QUARTER', 'YEAR'] as const).map(tf => (
                                    <button
                                      key={tf}
                                      onClick={() => { setDistTimeframe(tf); setHoveredDistTrade(null); }}
                                      className={`px-1.5 sm:px-2 py-0.5 text-[8.5px] sm:text-[9px] font-mono font-bold rounded-md transition-all whitespace-nowrap ${
                                        distTimeframe === tf
                                          ? 'bg-accent/20 text-accent border border-accent/40 shadow-sm font-black'
                                          : 'text-dim hover:text-primary font-medium'
                                      }`}
                                    >"""
new_tf = """<div className="flex items-center bg-primary/[0.04] p-1 rounded-xl border border-primary/10 overflow-x-auto hide-scrollbar shadow-inner">
                                  {(['TODAY', 'WEEK', 'MONTH', 'QUARTER', 'YEAR'] as const).map(tf => (
                                    <button
                                      key={tf}
                                      onClick={() => { setDistTimeframe(tf); setHoveredDistTrade(null); }}
                                      className={`px-2.5 sm:px-3 py-1 text-[9.5px] sm:text-[10px] font-mono rounded-lg transition-all whitespace-nowrap ${
                                        distTimeframe === tf
                                          ? 'bg-primary text-secondary font-black shadow-md scale-[1.02] border border-primary/10'
                                          : 'text-primary/60 hover:text-primary font-bold hover:bg-primary/5'
                                      }`}
                                    >"""
content = content.replace(old_tf, new_tf)

# 2. Update the Unit Selector
old_unit = """<div className="flex items-center bg-secondary/40 p-0.5 rounded-lg border border-primary/15">
                                  <button
                                    onClick={() => setDistUnit('CURRENCY')}
                                    className={`px-1.5 py-0.5 text-[9px] font-mono font-bold rounded-md transition-all ${
                                      distUnit === 'CURRENCY'
                                        ? 'bg-accent/20 text-accent border border-accent/40 shadow-sm font-black'
                                        : 'text-dim hover:text-primary font-medium'
                                    }`}
                                  >
                                    ₹
                                  </button>
                                  <button
                                    onClick={() => setDistUnit('PERCENT')}
                                    className={`px-1.5 py-0.5 text-[9px] font-mono font-bold rounded-md transition-all ${
                                      distUnit === 'PERCENT'
                                        ? 'bg-accent/20 text-accent border border-accent/40 shadow-sm font-black'
                                        : 'text-dim hover:text-primary font-medium'
                                    }`}
                                  >"""
new_unit = """<div className="flex items-center bg-primary/[0.04] p-1 rounded-xl border border-primary/10 shadow-inner">
                                  <button
                                    onClick={() => setDistUnit('CURRENCY')}
                                    className={`px-3 py-1 text-[11px] font-mono rounded-lg transition-all ${
                                      distUnit === 'CURRENCY'
                                        ? 'bg-primary text-secondary font-black shadow-md scale-[1.02] border border-primary/10'
                                        : 'text-primary/60 hover:text-primary font-bold hover:bg-primary/5'
                                    }`}
                                  >
                                    ₹
                                  </button>
                                  <button
                                    onClick={() => setDistUnit('PERCENT')}
                                    className={`px-3 py-1 text-[11px] font-mono rounded-lg transition-all ${
                                      distUnit === 'PERCENT'
                                        ? 'bg-primary text-secondary font-black shadow-md scale-[1.02] border border-primary/10'
                                        : 'text-primary/60 hover:text-primary font-bold hover:bg-primary/5'
                                    }`}
                                  >"""
content = content.replace(old_unit, new_unit)

# 3. Update LIVE P&L badge
old_badge = """<span className="text-[8px] font-mono font-bold px-1.5 py-0.2 rounded-full bg-accent/15 text-accent border border-accent/30 not-italic uppercase">
                                    Live P&L
                                  </span>"""
new_badge = """<span className="text-[8px] font-mono font-black px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 not-italic uppercase">
                                    LIVE P&L
                                  </span>"""
content = content.replace(old_badge, new_badge)

# 4. Make subtitle slightly stronger text-dim to text-primary/60
old_subtitle = 'p className="text-[8px] sm:text-[9px] font-mono font-bold tracking-wider text-dim uppercase"'
new_subtitle = 'p className="text-[8px] sm:text-[9px] font-mono font-bold tracking-wider text-primary/60 uppercase"'
content = content.replace(old_subtitle, new_subtitle)

with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
