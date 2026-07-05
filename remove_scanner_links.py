import glob
import os

html_files = glob.glob('/Users/vishant/Documents/Project/TLCS_Website_Deploy/*.html')

for file_path in html_files:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if 'href="scanner.html"' in line and 'AI Scanner' in line:
            continue
        new_lines.append(line)
        
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
