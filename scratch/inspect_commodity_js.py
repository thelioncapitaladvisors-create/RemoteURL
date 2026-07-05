with open('TLCS_Website_Deploy/commodity-scanner.js', 'r') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'symstat' in line.lower() or 'symsigs' in line.lower():
        print(f'{idx+1}: {line.strip()}')
