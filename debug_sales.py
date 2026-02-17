from odata_client import ODataClient
import pandas as pd

client = ODataClient()
print("--- DIAGNOSTIC VENTES ---")

# 1. Check Game Status
print("\n1. Statut du Jeu (Current_Game_Rules)")
try:
    df_rules = client.fetch_view("Current_Game_Rules", top=5)
    if not df_rules.empty:
        print(df_rules[['ROW_ID', 'GAME', 'SCENARIO', 'ELAPSED_TIME', 'ROUND']].to_string())
    else:
        print("⚠ Aucune règle de jeu trouvée.")
except Exception as e:
    print(f"Erreur: {e}")

# 2. Check Sales
print("\n2. Données Ventes (Sales)")
try:
    df_sales = client.fetch_view("Sales", top=5)
    if not df_sales.empty:
        print(f"✓ {len(df_sales)} lignes trouvées.")
        print(df_sales.head().to_string())
    else:
        print("⚠ Table 'Sales' VIDE. (Aucune vente enregistrée pour cet utilisateur)")
except Exception as e:
    print(f"Erreur: {e}")

# 3. Check Market
print("\n3. Données Marché (Market)")
try:
    df_market = client.fetch_view("Market", top=5)
    if not df_market.empty:
        print(f"✓ {len(df_market)} lignes trouvées.")
    else:
        print("⚠ Table 'Market' VIDE. (Aucune activité marché globale)")
except Exception as e:
    print(f"Erreur: {e}")
