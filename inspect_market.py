from odata_client import ODataClient
import pandas as pd

client = ODataClient()
print("Fetching Market view...")
try:
    df = client.fetch_view("Market", top=50)

    if df.empty:
        print("DataFrame is empty.")
    else:
        print(f"\nDataFrame shape: {df.shape}")
        print("\nColumns in Market view:")
        print(df.columns.tolist())
        print("\nFirst row sample:")
        print(df.iloc[0])
except Exception as e:
    print(f"Error fetching Market view: {e}")
