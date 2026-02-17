"""
Analyseur de données ERPsim
"""

import pandas as pd
from odata_client import ODataClient
from config import settings
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ERPSimAnalyzer:
    """Analyseur de données ERPsim"""

    def __init__(self):
        self.client = ODataClient()
        self.company_code = settings.COMPANY_CODE
        self.cache = {}

    def get_company_valuation(self) -> pd.DataFrame:
        """Récupère la valorisation de l'entreprise"""
        if 'valuation' not in self.cache:
            self.cache['valuation'] = self.client.fetch_view(
                "Company_Valuation",
                top=1000
            )
        return self.cache['valuation']

    def get_sales_summary(self) -> pd.DataFrame:
        """Récupère le résumé des ventes"""
        if 'sales' not in self.cache:
            df = self.client.fetch_view("Sales", top=10000)

            if df.empty:
                return df

            # Convertir en types corrects
            if 'QUANTITY' in df.columns:
                df['QUANTITY'] = pd.to_numeric(df['QUANTITY'], errors='coerce')
            if 'NET_VALUE' in df.columns:
                df['NET_VALUE'] = pd.to_numeric(df['NET_VALUE'], errors='coerce')
            if 'COST' in df.columns:
                df['COST'] = pd.to_numeric(df['COST'], errors='coerce')

            # Agrégation par produit
            # On groupe aussi par MATERIAL_NUMBER pour le garder
            group_cols = ['MATERIAL_NUMBER', 'MATERIAL_DESCRIPTION'] if 'MATERIAL_NUMBER' in df.columns else ['MATERIAL_DESCRIPTION']
            
            summary = df.groupby(group_cols).agg({
                'QUANTITY': 'sum',
                'NET_VALUE': 'sum',
                'COST': 'sum'
            }).reset_index()

            summary['AVG_PRICE'] = summary['NET_VALUE'] / summary['QUANTITY']
            summary['PROFIT'] = summary['NET_VALUE'] - summary['COST']
            summary['MARGIN_PCT'] = (summary['PROFIT'] / summary['NET_VALUE'] * 100).round(2)

            self.cache['sales'] = summary.sort_values('NET_VALUE', ascending=False)

        return self.cache['sales']

    def get_sales_by_area(self) -> pd.DataFrame:
        """Ventes par zone géographique"""
        df = self.client.fetch_view("Sales", top=10000)

        if df.empty:
            return df

        # Convertir en types corrects
        if 'QUANTITY' in df.columns:
            df['QUANTITY'] = pd.to_numeric(df['QUANTITY'], errors='coerce')
        if 'NET_VALUE' in df.columns:
            df['NET_VALUE'] = pd.to_numeric(df['NET_VALUE'], errors='coerce')
        if 'COST' in df.columns:
            df['COST'] = pd.to_numeric(df['COST'], errors='coerce')

        summary = df.groupby('AREA').agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()

        summary['PROFIT'] = summary['NET_VALUE'] - summary['COST']
        summary['MARGIN_PCT'] = (summary['PROFIT'] / summary['NET_VALUE'] * 100).round(2)

        return summary



    def get_sales_by_product_and_area(self) -> pd.DataFrame:
        """Ventes par produit et zone avec détails (Marge, Prix)"""
        df = self.client.fetch_view("Sales", top=10000)

        if df.empty:
            return df

        # Convertir types
        for col in ['NET_VALUE', 'COST', 'QUANTITY']:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # GroupBy Produit et Zone
        group_cols = ['MATERIAL_NUMBER', 'MATERIAL_DESCRIPTION', 'AREA'] if 'MATERIAL_NUMBER' in df.columns else ['MATERIAL_DESCRIPTION', 'AREA']
        
        summary = df.groupby(group_cols).agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()
        
        # Métriques calculées
        summary['PROFIT'] = summary['NET_VALUE'] - summary['COST']
        summary['MARGIN_PCT'] = (summary['PROFIT'] / summary['NET_VALUE'] * 100).fillna(0).round(1)
        summary['AVG_PRICE'] = (summary['NET_VALUE'] / summary['QUANTITY']).fillna(0).round(2)
        summary['AVG_COST'] = (summary['COST'] / summary['QUANTITY']).fillna(0).round(2)

        return summary

    def get_sales_by_product_and_dc(self) -> pd.DataFrame:
        """Ventes par produit et canal avec détails (Marge, Prix)"""
        df = self.client.fetch_view("Sales", top=10000)

        if df.empty:
            return df

        # Convertir types
        for col in ['NET_VALUE', 'COST', 'QUANTITY']:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # GroupBy Produit et DC
        group_cols = ['MATERIAL_NUMBER', 'MATERIAL_DESCRIPTION', 'DISTRIBUTION_CHANNEL'] if 'MATERIAL_NUMBER' in df.columns else ['MATERIAL_DESCRIPTION', 'DISTRIBUTION_CHANNEL']
        
        summary = df.groupby(group_cols).agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()
        
        # Métriques calculées
        summary['PROFIT'] = summary['NET_VALUE'] - summary['COST']
        summary['MARGIN_PCT'] = (summary['PROFIT'] / summary['NET_VALUE'] * 100).fillna(0).round(1)
        summary['AVG_PRICE'] = (summary['NET_VALUE'] / summary['QUANTITY']).fillna(0).round(2)
        
        # Renommer les canaux
        dc_names = {
            '10': 'Hypermarkets (DC10)',
            '12': 'Grocery (DC12)',
            '14': 'Convenience (DC14)'
        }
        summary['DISTRIBUTION_CHANNEL'] = summary['DISTRIBUTION_CHANNEL'].map(
            lambda x: dc_names.get(str(x), f"DC{x}")
        )

        return summary

    def get_sales_by_dc(self) -> pd.DataFrame:
        """Ventes par canal de distribution"""
        df = self.client.fetch_view("Sales", top=10000)

        if df.empty:
            return df

        # Convertir en types corrects
        if 'QUANTITY' in df.columns:
            df['QUANTITY'] = pd.to_numeric(df['QUANTITY'], errors='coerce')
        if 'NET_VALUE' in df.columns:
            df['NET_VALUE'] = pd.to_numeric(df['NET_VALUE'], errors='coerce')
        if 'COST' in df.columns:
            df['COST'] = pd.to_numeric(df['COST'], errors='coerce')

        summary = df.groupby('DISTRIBUTION_CHANNEL').agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()

        summary['PROFIT'] = summary['NET_VALUE'] - summary['COST']
        summary['MARGIN_PCT'] = (summary['PROFIT'] / summary['NET_VALUE'] * 100).round(2)

        # Renommer les canaux
        dc_names = {
            '10': 'Hypermarkets (DC10)',
            '12': 'Grocery (DC12)',
            '14': 'Convenience (DC14)'
        }
        summary['DISTRIBUTION_CHANNEL'] = summary['DISTRIBUTION_CHANNEL'].map(
            lambda x: dc_names.get(str(x), f"DC{x}")
        )

        return summary

    def get_current_inventory(self) -> pd.DataFrame:
        """Récupère l'inventaire actuel"""
        df = self.client.fetch_view("Current_Inventory", top=10000)

        if not df.empty and 'STOCK' in df.columns:
            df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce')
            if 'RESTRICTED' in df.columns:
                df['RESTRICTED'] = pd.to_numeric(df['RESTRICTED'], errors='coerce')
                df['AVAILABLE'] = df['STOCK'] - df['RESTRICTED']

        return df

    def get_current_inventory_kpi(self) -> pd.DataFrame:
        """Récupère les KPIs d'inventaire"""
        return self.client.fetch_view("Current_Inventory_KPI", top=10000)

    def get_market_data(self) -> pd.DataFrame:
        """Récupère les données de marché"""
        return self.client.fetch_view("Market", top=10000)

    def get_market_analysis(self) -> pd.DataFrame:
        """
        Compare les ventes de l'entreprise avec le marché (Zmarket).
        Calcule la part de marché et identifie les produits gagnants.
        """
        # 1. Récupérer les données
        market_df = self.get_market_data()
        company_sales = self.get_sales_summary()
        
        if market_df.empty:
            return pd.DataFrame()
            
        # 2. Nettoyer Market Data
        # On suppose que Market contient tout le marché (concurrents + nous)
        # Colonnes attendues: MATERIAL_NUMBER, NET_VALUE (ou PRICE * QUANTITY)
        
        if 'NET_VALUE' in market_df.columns:
            market_df['NET_VALUE'] = pd.to_numeric(market_df['NET_VALUE'], errors='coerce')
        elif 'PRICE' in market_df.columns and 'QUANTITY' in market_df.columns:
            market_df['NET_VALUE'] = pd.to_numeric(market_df['PRICE'], errors='coerce') * pd.to_numeric(market_df['QUANTITY'], errors='coerce')
        
        # Validation des colonnes (Nettoyage des noms)
        # On renomme d'abord pour être sûr
        market_df = market_df.rename(columns=lambda x: x.strip())
        
        logger.info(f"Market Columns: {market_df.columns.tolist()}")
        
        if 'MATERIAL_NUMBER' not in market_df.columns:
            logger.warning("MATERIAL_NUMBER manquant dans Market Data")
            return pd.DataFrame()
            
        if 'NET_VALUE' not in market_df.columns:
            logger.warning("NET_VALUE manquant dans Market Data")
            return pd.DataFrame()
        
        try:
            # Agrégation Marché par produit
            market_summary = market_df.groupby('MATERIAL_NUMBER')['NET_VALUE'].sum().reset_index()
            market_summary.rename(columns={'NET_VALUE': 'MARKET_VALUE'}, inplace=True)
        except Exception as e:
            logger.error(f"Erreur GroupBy Market: {e}")
            return pd.DataFrame()
        
        # 3. Fusionner avec nos ventes
        # On utilise company_sales qui est déjà agrégé par produit
        if company_sales.empty:
             analysis = market_summary.copy()
             analysis['MY_VALUE'] = 0
             analysis['MARKET_SHARE'] = 0
        else:
            analysis = pd.merge(market_summary, 
                                company_sales[['MATERIAL_NUMBER', 'MATERIAL_DESCRIPTION', 'NET_VALUE']], 
                                on='MATERIAL_NUMBER', 
                                how='left')
            analysis.rename(columns={'NET_VALUE': 'MY_VALUE'}, inplace=True)
            analysis['MY_VALUE'] = analysis['MY_VALUE'].fillna(0)
            
        # 4. Calculs KPIs
        # Part de marché
        analysis['MARKET_SHARE'] = (analysis['MY_VALUE'] / analysis['MARKET_VALUE'] * 100).fillna(0).round(1)
        
        # Classification
        # Star: Gros marché + Grosse part
        # Opportunity: Gros marché + Petite part
        # Niche: Petit marché + Grosse part
        # Dog: Petit marché + Petite part
        
        median_market = analysis['MARKET_VALUE'].median()
        median_share = analysis['MARKET_SHARE'].median()
        
        def classify(row):
            if row['MARKET_VALUE'] >= median_market:
                if row['MARKET_SHARE'] >= median_share:
                    return "⭐ Star"
                else:
                    return "🎯 Opportunité"
            else:
                if row['MARKET_SHARE'] >= median_share:
                    return "🛡️ Niche"
                else:
                    return "💤 Faible"
                    
        analysis['STATUS'] = analysis.apply(classify, axis=1)
        
        return analysis.sort_values('MARKET_VALUE', ascending=False)

    def get_production_orders(self) -> pd.DataFrame:
        """Récupère les ordres de production"""
        df = self.client.fetch_view("Production_Orders", top=10000)

        if not df.empty:
            if 'TARGET_QUANTITY' in df.columns:
                df['TARGET_QUANTITY'] = pd.to_numeric(df['TARGET_QUANTITY'], errors='coerce')
            if 'CONFIRMED_QUANTITY' in df.columns:
                df['CONFIRMED_QUANTITY'] = pd.to_numeric(df['CONFIRMED_QUANTITY'], errors='coerce')
                df['PROGRESS_PCT'] = (
                    df['CONFIRMED_QUANTITY'] / df['TARGET_QUANTITY'] * 100
                ).round(2)

        return df

    def get_purchase_orders(self) -> pd.DataFrame:
        """Récupère les commandes d'achat"""
        return self.client.fetch_view("Purchase_Orders", top=10000)

    def get_financial_data(self) -> pd.DataFrame:
        """Récupère les données financières"""
        return self.client.fetch_view("Financial_Postings", top=10000)

    def print_summary(self):
        """Affiche un résumé dans le terminal"""
        print("\n" + "="*70)
        print(f"📊 ANALYSE ERPSIM - ORGANISATION {self.company_code}")
        print("="*70 + "\n")

        # Valorisation
        valuation_df = self.get_company_valuation()
        if not valuation_df.empty:
            last_val = valuation_df.iloc[-1]
            print("💰 VALORISATION ENTREPRISE")
            if 'COMPANY_VALUATION' in last_val:
                print(f"   Company Valuation: €{float(last_val.get('COMPANY_VALUATION', 0)):,.2f}")
            if 'CREDIT_RATING' in last_val:
                print(f"   Credit Rating: {last_val.get('CREDIT_RATING', 'N/A')}")
            if 'PROFIT' in last_val:
                print(f"   Profit Total: €{float(last_val.get('PROFIT', 0)):,.2f}")
            if 'BANK_CASH_ACCOUNT' in last_val:
                print(f"   Cash: €{float(last_val.get('BANK_CASH_ACCOUNT', 0)):,.2f}")
            if 'BANK_LOAN' in last_val:
                print(f"   Loan: €{float(last_val.get('BANK_LOAN', 0)):,.2f}")
        else:
            print("⚠ Aucune donnée de valorisation disponible")

        print("\n" + "-"*70 + "\n")

        # Top produits
        sales_summary = self.get_sales_summary()
        if not sales_summary.empty:
            print("🏆 TOP 5 PRODUITS PAR REVENUS")
            top5 = sales_summary.head(5)
            for idx, row in top5.iterrows():
                print(f"   {row['MATERIAL_DESCRIPTION'][:40]:<40} "
                      f"€{row['NET_VALUE']:>12,.0f} "
                      f"({row['MARGIN_PCT']:>5.1f}% marge)")
        else:
            print("⚠ Aucune donnée de vente disponible")

        print("\n" + "-"*70 + "\n")

        # Ventes par zone
        sales_by_area = self.get_sales_by_area()
        if not sales_by_area.empty:
            print("🌍 VENTES PAR ZONE")
            for idx, row in sales_by_area.iterrows():
                print(f"   {row['AREA']:<10} €{row['NET_VALUE']:>12,.0f} "
                      f"({row['MARGIN_PCT']:>5.1f}%)")
        else:
            print("⚠ Aucune donnée par zone")

        print("\n" + "-"*70 + "\n")

        # Ventes par canal
        sales_by_dc = self.get_sales_by_dc()
        if not sales_by_dc.empty:
            print("📦 VENTES PAR CANAL DE DISTRIBUTION")
            for idx, row in sales_by_dc.iterrows():
                print(f"   {row['DISTRIBUTION_CHANNEL']:<25} €{row['NET_VALUE']:>12,.0f} "
                      f"({row['MARGIN_PCT']:>5.1f}%)")
        else:
            print("⚠ Aucune donnée par canal")

        print("\n" + "-"*70 + "\n")

        # Inventaire
        inventory = self.get_current_inventory()
        if not inventory.empty:
            finished_goods = inventory[inventory['STORAGE_LOCATION'] == '02'] if 'STORAGE_LOCATION' in inventory.columns else inventory
            total_stock = finished_goods['STOCK'].sum() if 'STOCK' in finished_goods.columns else 0
            print(f"📦 INVENTAIRE PRODUITS FINIS")
            print(f"   Total en stock: {int(total_stock):,} unites")
            print(f"   Nombre de produits: {len(finished_goods)}")
        else:
            print("⚠ Aucune donnée d'inventaire disponible")

        print("\n" + "="*70 + "\n")

    def generate_performance_report(self) -> Dict[str, pd.DataFrame]:
        """Génère un rapport de performance complet"""
        logger.info("Génération du rapport de performance...")

        report = {
            'valuation': self.get_company_valuation(),
            'sales_summary': self.get_sales_summary(),
            'sales_by_area': self.get_sales_by_area(),
            'sales_by_dc': self.get_sales_by_dc(),
            'inventory': self.get_current_inventory(),
            'production': self.get_production_orders(),
            'purchases': self.get_purchase_orders()
        }

        return report
