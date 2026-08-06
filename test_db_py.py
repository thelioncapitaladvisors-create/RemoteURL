import os
import json
import urllib.request
import urllib.error

env_vars = {}
with open("/Users/vishant/Documents/Project/TLCS_Website_Deploy/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_vars[k.strip()] = v.strip().strip("'").strip('"')

url = f"{env_vars['SUPABASE_URL']}/rest/v1/signals?select=id,symbol,status,outcome,metadata,created_at&limit=5&order=created_at.desc"
headers = {
    "apikey": env_vars['SUPABASE_SERVICE_ROLE_KEY'],
    "Authorization": f"Bearer {env_vars['SUPABASE_SERVICE_ROLE_KEY']}"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("SIGNALS:")
        print(json.dumps(data, indent=2))
except urllib.error.URLError as e:
    print(f"Error: {e}")
