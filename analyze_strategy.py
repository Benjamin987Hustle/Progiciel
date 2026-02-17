
import pandas as pd
import numpy as np
from analyzer import ERPSimAnalyzer
from config import settings

def detailed_analysis():
    print("[INFO] Starting Deep Analysis...")
    analyzer = ERPSimAnalyzer()
    
    # 1. Sales & Margin Analysis
    sales = analyzer.get_sales_summary()
    if sales.empty:
        print("[WARN] No sales data found.")
        return

    # Calculate contribution to total profit
    total_profit = sales['PROFIT'].sum()
    sales['PROFIT_CONTRIBUTION'] = (sales['PROFIT'] / total_profit * 100).round(2)
    
    print("\n--- PRODUCT PORTFOLIO ANALYSIS ---")
    print(sales[['MATERIAL_DESCRIPTION', 'NET_VALUE', 'MARGIN_PCT', 'PROFIT_CONTRIBUTION']].to_string())

    # Identify "Stars" (High Margin, High Vol) and "Dogs" (Low Margin, Low Vol)
    avg_margin = sales['MARGIN_PCT'].mean()
    avg_turnover = sales['NET_VALUE'].mean()
    
    stars = sales[(sales['MARGIN_PCT'] >= avg_margin) & (sales['NET_VALUE'] >= avg_turnover)]
    dogs = sales[(sales['MARGIN_PCT'] < avg_margin) & (sales['NET_VALUE'] < avg_turnover)]
    cash_cows = sales[(sales['MARGIN_PCT'] < avg_margin) & (sales['NET_VALUE'] >= avg_turnover)]
    question_marks = sales[(sales['MARGIN_PCT'] >= avg_margin) & (sales['NET_VALUE'] < avg_turnover)]

    print(f"\n STARS (Keep pushing): {len(stars)}")
    if not stars.empty:
        print(stars['MATERIAL_DESCRIPTION'].tolist())
        
    print(f"\n DOGS (Drop or Reprice): {len(dogs)}")
    if not dogs.empty:
        print(dogs['MATERIAL_DESCRIPTION'].tolist())

    # 2. Regional Analysis
    print("\n--- REGIONAL STRATEGY ---")
    regional = analyzer.get_sales_by_area()
    if not regional.empty:
        best_region = regional.loc[regional['PROFIT'].idxmax()]
        print(f" Most Profitable Region: {best_region['AREA']} ({best_region['PROFIT']:,.0f})")
        
        # Breakdown by channel
        dc_sales = analyzer.get_sales_by_dc()
        print("\nCHANNEL PERFORMANCE:")
        print(dc_sales[['DISTRIBUTION_CHANNEL', 'MARGIN_PCT', 'NET_VALUE']].to_string())

    # 3. Inventory & Bottlenecks
    print("\n--- INVENTORY HEALTH ---")
    inventory = analyzer.get_current_inventory()
    if not inventory.empty and 'STOCK' in inventory.columns:
        # Check for stockouts (Zero stock) - assuming this is current state
        stockouts = inventory[inventory['STOCK'] == 0]
        if not stockouts.empty:
            print(f" STOCKOUTS DETECTED: {len(stockouts)} products")
            print(stockouts['MATERIAL_NUMBER'].tolist())
        else:
            print(" No current stockouts.")
    
    # 4. Generate Strategy Text
    with open("STRATEGY_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 Stratégie Gagnante ERPsim\n\n")
        
        f.write("## 1. Analyse du Portfolio\n")
        f.write(f"- **Total Revenue:** €{sales['NET_VALUE'].sum():,.2f}\n")
        f.write(f"- **Total Profit:** €{total_profit:,.2f}\n\n")
        
        f.write("### 🔥 Produits Stars (A Prioriser)\n")
        for _, row in stars.iterrows():
            f.write(f"- **{row['MATERIAL_DESCRIPTION']}**: Marge {row['MARGIN_PCT']}% | Profit {row['PROFIT_CONTRIBUTION']}%\n")
            
        f.write("\n### 📉 Produits à Optimiser (Dogs/Question Marks)\n")
        for _, row in dogs.iterrows():
            f.write(f"- **{row['MATERIAL_DESCRIPTION']}**: Marge faible ({row['MARGIN_PCT']}%) -> Augmenter prix ou arrêter pub.\n")
            
        f.write("\n## 2. Stratégie de Prix & Canaux\n")
        if not dc_sales.empty:
            best_dc = dc_sales.loc[dc_sales['MARGIN_PCT'].idxmax()]
            f.write(f"- **Canal le plus rentable:** {best_dc['DISTRIBUTION_CHANNEL']} ({best_dc['MARGIN_PCT']}%) -> Focaliser les produits à forte marge ici.\n")
            
        f.write("\n## 3. Plan d'Action Recommandé\n")
        f.write("1. **Augmenter les prix** sur les 'Stars' de 2-5% pour tester l'élasticité.\n")
        f.write("2. **Couper le marketing** sur les 'Dogs' et liquider le stock.\n")
        f.write("3. **Investir massivement** dans la région " + (best_region['AREA'] if not regional.empty else "la plus performante") + ".\n")

    print("\n[SUCCESS] Strategy report generated: STRATEGY_REPORT.md")

if __name__ == "__main__":
    detailed_analysis()
