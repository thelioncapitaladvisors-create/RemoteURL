import urllib.request
import json
import urllib.parse

# Correct PostgREST syntax for spaces in IN array is to use double quotes around the elements
url = 'https://dwepduvhzuhzeehbeaaz.supabase.co/rest/v1/signals?status=in.(%22ACTIVE%20LIMIT%22,%22Active%20Limit%22)'
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

payload = {"status": "CANCELLED", "outcome": "CANCELLED"}
data = json.dumps(payload).encode('utf-8')

req = urllib.request.Request(url, data=data, headers=headers, method='PATCH')
try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        print(f"Healed {len(res_data)} stuck ACTIVE LIMIT trades.")
except Exception as e:
    print(f"Error: {e}")
