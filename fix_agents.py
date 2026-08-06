import re

filepath = '/Users/vishant/Documents/Project/.agents/AGENTS.md'
with open(filepath, 'r') as f:
    content = f.read()

content = re.sub(r'function resolveOutcome\(s\) \{\n    const st = \(s\.status', 'function resolveOutcome(s) {\n    if (!s) return \'OPEN\';\n    const st = (s.status', content)

with open(filepath, 'w') as f:
    f.write(content)
