import re

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

old_filter = """                       const todaysTableSignals = uniqueSignals.filter(s => {
                         const o = resolveOutcome(s);
                         if (o === 'CANCELLED') return false;
                         const sigTime = new Date(s.signal_ts || s.created_at);
                         if (isNaN(sigTime.getTime())) return false;
                         return sigTime.getTime() >= startOfToday;
                       });"""

new_filter = """                       const todaysTableSignals = uniqueSignals.filter(s => {
                         const o = resolveOutcome(s);
                         if (o !== 'WIN' && o !== 'LOSS') return false;
                         const sigTime = new Date(s.signal_ts || s.created_at);
                         if (isNaN(sigTime.getTime())) return false;
                         return sigTime.getTime() >= startOfToday;
                       });"""
content = content.replace(old_filter, new_filter)


old_sort = """                       todaysTableSignals.sort((a, b) => {
                         const mA = getMarket(a);
                         const mB = getMarket(b);
                         const idxA = marketOrder.indexOf(mA);
                         const idxB = marketOrder.indexOf(mB);
                         if (idxA !== idxB) return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
                         return new Date(a.signal_ts || a.created_at).getTime() - new Date(b.signal_ts || b.created_at).getTime();
                       });"""

new_sort = """                       todaysTableSignals.sort((a, b) => {
                         const mA = getMarket(a);
                         const mB = getMarket(b);
                         const idxA = marketOrder.indexOf(mA);
                         const idxB = marketOrder.indexOf(mB);
                         if (idxA !== idxB) return (idxA === -1 ? 99 : idxA) - (idxB === -1 ? 99 : idxB);
                         const exactA = getExactPct(a) || 0;
                         const exactB = getExactPct(b) || 0;
                         return exactB - exactA;
                       });"""

content = content.replace(old_sort, new_sort)

with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
