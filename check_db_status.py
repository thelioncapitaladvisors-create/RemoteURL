import urllib.request
import json
url = "https://dwepduvhzuhzeehbeaaz.supabase.co/rest/v1/signals?select=id,symbol,status,created_at&limit=50&order=created_at.desc"
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"
}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    status_counts = {}
    for d in data:
        status_counts[d['status']] = status_counts.get(d['status'], 0) + 1
    print("Recent 50 trades status counts:", status_counts)
    
    # print the ones that have ACTIVE or OPEN or LIMIT in their status
    for d in data:
        if 'ACTIVE' in d['status'].upper() or 'OPEN' in d['status'].upper() or 'LIMIT' in d['status'].upper():
            print(d)
