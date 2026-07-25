import os
import pandas as pd
from dotenv import load_dotenv
from dhanhq import dhanhq, DhanContext

load_dotenv()
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

print("Fetching security list...")
try:
    # Actually, Dhan provides a daily csv file at:
    # https://images.dhan.co/api-data/api-scrip-master.csv
    df = pd.read_csv("https://images.dhan.co/api-data/api-scrip-master.csv", low_memory=False)
    mcx = df[df['SEM_EXM_EXCH_ID'] == 'MCX']
    crude = mcx[mcx['SEM_TRADING_SYMBOL'].str.contains('CRUDEOIL', na=False)]
    print(crude[['SEM_SMST_SECURITY_ID', 'SEM_TRADING_SYMBOL', 'SEM_INSTRUMENT_NAME', 'SEM_EXPIRY_DATE']].head(10))
except Exception as e:
    print(f"Failed: {e}")
