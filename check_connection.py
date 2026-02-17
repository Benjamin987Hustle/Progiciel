from odata_client import ODataClient
import pandas as pd

client = ODataClient()
print("Testing connection...")
if client.test_connection():
    print("Connection successful!")
    print("Fetching Game Rules to check round...")
    try:
        df = client.fetch_view("Current_Game_Rules", top=1)
        if not df.empty:
            print("\n--- GAME STATUS ---")
            print(df.iloc[0].to_string())
        else:
            print("Connected, but 'Current_Game_Rules' is empty. Simulation might be stopped or resetting.")
    except Exception as e:
        print(f"Error fetching game rules: {e}")
else:
    print("Connection failed.")
