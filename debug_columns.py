from odata_client import ODataClient
import pandas as pd

client = ODataClient()

print("--- Market Columns ---")
try:
    df_market = client.fetch_view("Market", top=1)
    print(df_market.columns.tolist())
    if not df_market.empty:
        print(df_market.iloc[0])
except Exception as e:
    print(e)

print("\n--- Current_Pricing_Conditions Columns ---")
try:
    df_pricing = client.fetch_view("Current_Pricing_Conditions", top=1)
    print(df_pricing.columns.tolist())
    if not df_pricing.empty:
        print(df_pricing.iloc[0])
except Exception as e:
    print(e)
