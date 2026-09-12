import re

with open('TLCS_Website_Deploy/blog.html', 'r') as f:
    content = f.read()

old_css = """
        .dist-tf-btn.active, .dist-unit-btn.active {
            background: rgba(255,255,255,0.15);
            color: #ffffff;
        }"""
new_css = """
        .dist-tf-btn.active, .dist-unit-btn.active {
            background: #ffffff;
            color: #000000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            font-weight: 900;
        }"""
content = content.replace(old_css, new_css)

with open('TLCS_Website_Deploy/blog.html', 'w') as f:
    f.write(content)
