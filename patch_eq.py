import re

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

pattern_eq = re.compile(r'<div className="col-span-2 sm:col-span-3 md:col-span-4 p-3 sm:p-4 rounded-2xl border wc-card-neutral mt-2 overflow-hidden flex items-center justify-between">')
content = pattern_eq.sub(r'<div className="col-span-2 sm:col-span-4 border-t border-primary/10 pt-4 mt-2 overflow-hidden flex items-center justify-between">', content)

with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
