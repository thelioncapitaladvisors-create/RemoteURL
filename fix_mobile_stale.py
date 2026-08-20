with open('/Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    text = f.read()

old_code = """  const isSignalActiveForMarket = (s: Signal, now = new Date()): boolean => {
    if (!s) return false;
    const sym = s.symbol || '';
    const cat = getMarketCategory(sym).toLowerCase();
    const lastClose = getLastMarketCloseTs(cat, now);
    
    const o = resolveOutcome(s);
    if (o === 'OPEN') return true;"""

new_code = """  const isSignalActiveForMarket = (s: Signal, now = new Date()): boolean => {
    if (!s) return false;
    const sym = s.symbol || '';
    const cat = getMarketCategory(sym).toLowerCase();
    const lastClose = getLastMarketCloseTs(cat, now);
    
    const o = resolveOutcome(s);
    // Only executed open trades (has updated_at) persist infinitely until mathematically closed.
    // Limit orders (!updated_at) must fall through to the timestamp check to properly expire.
    if (o === 'OPEN' && s.updated_at) return true;"""

if old_code in text:
    print("Found and replaced!")
    text = text.replace(old_code, new_code)
else:
    print("Not found!")

with open('/Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(text)

