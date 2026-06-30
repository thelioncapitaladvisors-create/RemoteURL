with open('/Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js', 'r') as f:
    code = f.read()

# Let's count open/close braces
open_braces = code.count('{')
close_braces = code.count('}')
open_parens = code.count('(')
close_parens = code.count(')')
open_brackets = code.count('[')
close_brackets = code.count(']')

print(f"Braces: {open_braces} / {close_braces}")
print(f"Parens: {open_parens} / {close_parens}")
print(f"Brackets: {open_brackets} / {close_brackets}")
