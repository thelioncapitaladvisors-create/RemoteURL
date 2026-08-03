import sys

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

start_marker = "                     {/* ── PIVOTBOSS COMBINED SCANNER ─────────────────────────── */}"
end_marker = "                     {/* ── END PIVOTBOSS COMBINED SCANNER ─────────────────────── */}\n"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker) + len(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find scanner block")
    sys.exit(1)

scanner_block = content[start_idx:end_idx]
content = content[:start_idx] + content[end_idx:]

insert_marker = '<h2 className="text-xl font-black italic tracking-tighter uppercase text-primary">Analytics</h2>\n                      </div>\n                    </div>\n'

insert_idx = content.find(insert_marker)
if insert_idx == -1:
    print("Could not find insertion point")
    sys.exit(1)

insert_pos = insert_idx + len(insert_marker)
content = content[:insert_pos] + "                    \n" + scanner_block + content[insert_pos:]

with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
print("Scanner moved successfully")
