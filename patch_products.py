import re

with open('TLCS_Website_Deploy/products.html', 'r') as f:
    content = f.read()

# Add data-download and cursor:pointer
content = content.replace('<div class="platform-badge">', '<div class="platform-badge" data-download="true" style="cursor: pointer;">')

with open('TLCS_Website_Deploy/products.html', 'w') as f:
    f.write(content)
