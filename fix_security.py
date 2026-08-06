import re
with open("/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine", "r") as f:
    content = f.read()
content = re.sub(r'(=\s*)request\.security\(([^)]+)\)', r'\1f_decode(request.security(\2))', content)
with open("/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine", "w") as f:
    f.write(content)
