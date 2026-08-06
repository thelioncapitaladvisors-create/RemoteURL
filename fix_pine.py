import os

filepath = '/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine'
with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith(('acB', 'acS', 'rB', 'rS', 'sB', 'sS', 'odB', 'odS', 'fdB', 'fdS', 'aB', 'aS', 'fB', 'fS', 'fbB', 'fbS', 'rtB', 'rtS', 'cB', 'cS')) and '!= 0;' in line:
        # Split on the semicolon
        parts = line.split(';')
        if len(parts) == 2:
            new_lines.append(parts[0] + '\n')
            # The second part needs to maintain the same indentation (4 spaces)
            # Actually, `parts[0]` has 4 spaces of indentation. The second part should also have 4 spaces.
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + parts[1].strip() + '\n')
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(filepath, 'w') as f:
    f.writelines(new_lines)
