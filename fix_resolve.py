import os
import re

files = [
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js',
    '/Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx'
]

for fp in files:
    if not os.path.exists(fp):
        continue
    with open(fp, 'r') as f:
        content = f.read()
    
    content = re.sub(r'function resolveOutcome\(s\) \{\s*(?:if\s*\(\!s\)\s*return\s*[\'"]OPEN[\'"];\s*)*', 'function resolveOutcome(s) {\n    if (!s) return \'OPEN\';\n', content)
    
    with open(fp, 'w') as f:
        f.write(content)
