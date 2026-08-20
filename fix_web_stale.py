with open('/Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js', 'r') as f:
    text = f.read()

old_code = """        // Active/Open signals are always valid
        const out = window.resolveOutcome(s);
        if (out === 'OPEN') return true;"""

new_code = """        // Active/Open signals are always valid
        const out = window.resolveOutcome(s);
        // Only executed open trades (has updated_at) persist infinitely until mathematically closed.
        // Limit orders (!updated_at) must fall through to the timestamp check to properly expire.
        if (out === 'OPEN' && s.updated_at) return true;"""

if old_code in text:
    print("Found and replaced in trade-metrics.js!")
    text = text.replace(old_code, new_code)
else:
    print("Not found in trade-metrics.js!")

with open('/Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js', 'w') as f:
    f.write(text)

