#!/usr/bin/env python3
"""
Point d'entrée principal pour analyser votre simulation ERPsim
"""

from odata_client import ODataClient
from analyzer import ERPSimAnalyzer
from config import settings
import pandas as pd
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fonction principale"""

    print("\n" + "="*70)
    print("🚀 SYSTEME DE GESTION ERPSIM MANUFACTURING")
    print("="*70)
    print(f"📍 Organisation: {settings.COMPANY_CODE}")
    print(f"🏭 Plant: {settings.PLANT}")
    print(f"🔗 URL: {settings.ODATA_BASE_URL}\n")

    # Test de connexion
    client = ODataClient()
    if not client.test_connection():
        print("\n❌ Impossible de se connecter à l'API OData")
        print("Vérifiez votre fichier .env et vos identifiants\n")
        return

    # Créer l'analyseur
    analyzer = ERPSimAnalyzer()

    # Afficher le résumé initial
    analyzer.print_summary()

    # Menu interactif
    while True:
        print("\n" + "="*70)
        print("📋 QUE VOULEZ-VOUS FAIRE ?")
        print("="*70)
        print("1. Afficher le résumé complet")
        print("2. Analyser les ventes par produit")
        print("3. Analyser les ventes par zone")
        print("4. Analyser les ventes par canal (DC)")
        print("5. Voir l'inventaire détaillé")
        print("6. Voir les ordres de production")
        print("7. Voir les commandes d'achat")
        print("8. Exporter les données en Excel")
        print("9. Rafraichir les donnees")
        print("0. Quitter")
        print("="*70)

        choice = input("\nVotre choix (0-9): ").strip()

        if choice == '0':
            print("\n👋 Au revoir!\n")
            break

        elif choice == '1':
            analyzer.print_summary()

        elif choice == '2':
            df = analyzer.get_sales_summary()
            if not df.empty:
                print("\n📊 VENTES PAR PRODUIT\n")
                print(df.to_string(index=False))
            else:
                print("\n⚠ Aucune donnee disponible")

        elif choice == '3':
            df = analyzer.get_sales_by_area()
            if not df.empty:
                print("\n🌍 VENTES PAR ZONE\n")
                print(df.to_string(index=False))
            else:
                print("\n⚠ Aucune donnee disponible")

        elif choice == '4':
            df = analyzer.get_sales_by_dc()
            if not df.empty:
                print("\n📦 VENTES PAR CANAL DE DISTRIBUTION\n")
                print(df.to_string(index=False))
            else:
                print("\n⚠ Aucune donnee disponible")

        elif choice == '5':
            df = analyzer.get_current_inventory()
            if not df.empty:
                print("\n📦 INVENTAIRE DETAILLE\n")
                cols = ['MATERIAL_DESCRIPTION', 'STORAGE_LOCATION', 'STOCK']
                if 'AVAILABLE' in df.columns:
                    cols.append('AVAILABLE')
                display_cols = [c for c in cols if c in df.columns]
                print(df[display_cols].to_string(index=False))
            else:
                print("\n⚠ Aucune donnee disponible")

        elif choice == '6':
            df = analyzer.get_production_orders()
            if not df.empty:
                print("\n⚙ ORDRES DE PRODUCTION\n")
                cols = ['PRODUCTION_ORDER', 'MATERIAL_NUMBER', 'TARGET_QUANTITY',
                        'CONFIRMED_QUANTITY', 'BEGIN_ROUND', 'END_ROUND']
                if 'PROGRESS_PCT' in df.columns:
                    cols.append('PROGRESS_PCT')
                display_cols = [c for c in cols if c in df.columns]
                print(df[display_cols].to_string(index=False))
            else:
                print("\n⚠ Aucune donnee disponible")

        elif choice == '7':
            df = analyzer.get_purchase_orders()
            if not df.empty:
                print("\n🛒 COMMANDES D'ACHAT\n")
                cols = ['PURCHASING_ORDER', 'VENDOR', 'MATERIAL_NUMBER', 'QUANTITY', 'STATUS']
                display_cols = [c for c in cols if c in df.columns]
                print(df[display_cols].to_string(index=False))
            else:
                print("\n⚠ Aucune donnee disponible")

        elif choice == '8':
            try:
                report = analyzer.generate_performance_report()
                filename = f"erpsim_report_{settings.COMPANY_CODE}.xlsx"

                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    for sheet_name, df in report.items():
                        if not df.empty:
                            # Limiter les colonnes pour Excel
                            cols_to_write = [c for c in df.columns if c != '__metadata']
                            df[cols_to_write].to_excel(writer, sheet_name=sheet_name[:31], index=False)

                print(f"\n✓ Rapport exporte: {filename}")
            except Exception as e:
                print(f"\n✗ Erreur lors de l'export: {e}")

        elif choice == '9':
            analyzer.cache = {}
            print("\n✓ Cache rafraichi")

        else:
            print("\n⚠ Choix invalide")


if __name__ == "__main__":
    main()
