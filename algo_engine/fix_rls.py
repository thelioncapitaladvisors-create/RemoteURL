import os
import psycopg2

print("Connecting to Supabase...")
conn = psycopg2.connect(
    host="db.dwepduvhzuhzeehbeaaz.supabase.co",
    port=5432,
    dbname="postgres",
    user="postgres",
    password="[&/e!WpE6P!GaMpc]"
)
cur = conn.cursor()

print("Applying RLS Fix...")
with open('/Users/vishant/Documents/Project/TLCS_Website_Deploy/SIGNALS_PUBLIC_READ_FIX.sql', 'r') as f:
    sql = f.read()

cur.execute(sql)
conn.commit()

print("Verifying RLS Policies...")
cur.execute("SELECT polname, polcmd, polroles FROM pg_policies WHERE tablename = 'signals';")
policies = cur.fetchall()
for p in policies:
    print(p)

cur.close()
conn.close()
print("Done!")
