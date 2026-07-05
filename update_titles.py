import os

def replace_title(file_path, old_title, new_title):
    with open(file_path, 'r') as f:
        content = f.read()
    content = content.replace(f'<title>{old_title}</title>', f'<title>{new_title}</title>')
    with open(file_path, 'w') as f:
        f.write(content)

replace_title('/Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.html', 'Alerts Scanner | The Lion Capital Solutions', 'AI Dashboard | The Lion Capital Solutions')
replace_title('/Users/vishant/Documents/Project/TLCS_Website_Deploy/metrics.html', 'Intelligence Terminal | The Lion Capital Solutions', 'AI Research | The Lion Capital Solutions')
