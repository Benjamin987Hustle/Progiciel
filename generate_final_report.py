
import pandas as pd
from analyzer import ERPSimAnalyzer
import os

def generate_report():
    print("[INFO] Initialisation de l'analyseur...")
    analyzer = ERPSimAnalyzer()
    
    print("[INFO] Récupération des données finales...")
    try:
        data = analyzer.generate_performance_report()
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération des données: {e}")
        return

    output_file = "Rapport_Final_ERPsim.xlsx"
    
    print(f"[INFO] Sauvegarde dans {output_file}...")
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Page de garde / Résumé
            summary_data = []
            
            # KPI: Valuation
            val_df = data.get('valuation')
            if not val_df.empty:
                last_val = val_df.iloc[-1]
                summary_data.append({"Métrique": "Valorisation Finale", "Valeur": last_val.get('COMPANY_VALUATION', 0)})
                summary_data.append({"Métrique": "Credit Rating", "Valeur": last_val.get('CREDIT_RATING', 'N/A')})
                summary_data.append({"Métrique": "Profit Total", "Valeur": last_val.get('PROFIT', 0)})
            
            # KPI: Sales
            sales_df = data.get('sales_summary')
            if not sales_df.empty:
                 total_rev = sales_df['NET_VALUE'].sum()
                 summary_data.append({"Métrique": "Chiffre d'Affaires Total", "Valeur": total_rev})
                 top_prod = sales_df.iloc[0]
                 summary_data.append({"Métrique": "Meilleur Produit", "Valeur": f"{top_prod['MATERIAL_DESCRIPTION']} (€{top_prod['NET_VALUE']:,.0f})"})

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="RESUME", index=False)
            
            # Autres feuilles
            for sheet_name, df in data.items():
                if not df.empty:
                    # Nettoyer les colonnes metadata
                    cols = [c for c in df.columns if not c.startswith('__')]
                    safe_name = sheet_name[:30]  # Excel limit 31 chars
                    df[cols].to_excel(writer, sheet_name=safe_name, index=False)
                    
        print(f"[SUCCESS] Rapport généré avec succès : {os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'écriture du fichier Excel: {e}")

if __name__ == "__main__":
    generate_report()
