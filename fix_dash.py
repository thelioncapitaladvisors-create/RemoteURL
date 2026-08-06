import re

filepath = '/Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html'
with open(filepath, 'r') as f:
    content = f.read()

content = re.sub(r'const resolveOutcome = \(s\) => \{\s*(?:if\s*\(\!s\)\s*return\s*[\'"]OPEN[\'"];\s*)*', 'const resolveOutcome = (s) => {\n                    if (!s) return \'OPEN\';\n', content)

with open(filepath, 'w') as f:
    f.write(content)
