"""
Moteur de décision pour les ventes
"""

import pandas as pd
from typing import Dict, Tuple
from odata_client import ODataClient
import logging

logger = logging.getLogger(__name__)


class SalesEngine:
    """Moteur de décision pour les ventes"""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.client = ODataClient()

    def get_active_products(self) -> list[str]:
        """
        Retourne la liste des produits actifs (ceux qui ont un prix défini).
        Utilisé pour filtrer le dashboard.
        """
        try:
            prices_df = self.client.fetch_view("Current_Pricing_Conditions", top=1000)
            if not prices_df.empty and 'MATERIAL_NUMBER' in prices_df.columns:
                 # Filtre simple: On suppose que les produits finis commencent par une lettre spécifique ou sont dans cette liste
                 # Dans ERPsim, seuls les produits finis ont un prix de vente défini par nous.
                return prices_df['MATERIAL_NUMBER'].dropna().unique().tolist()
                
            # Fallback (Mode Démo / Avant simulation)
            # On retourne la liste standard pour que l'interface ne soit pas vide
            return [
                "F01", "F02", "F03", "F04", "F05", "F06",
                "F10", "F11", "F12", "F13", "F14", "F15", "F16"
            ]
        except Exception as e:
            logger.error(f"Erreur recuperation produits actifs: {e}")
        return []

    def get_market_price_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """
        Calcule le prix moyen pondéré du marché par produit et canal
        Se base sur SALES_ORGANIZATION = 'Market'
        Note: Market view n'a pas MATERIAL_NUMBER, on doit mapper via Description.
        """
        market_df = self.client.fetch_view("Market", top=10000)
        # On a besoin d'une table de mapping Description -> Material Number
        # On utilise Current_Pricing_Conditions ou Products pour ça
        products_df = self.client.fetch_view("Current_Pricing_Conditions", top=1000)
        
        if market_df.empty:
            return {}
            
        # Créer le mapping Description -> Material Number
        desc_map = {}
        if not products_df.empty and 'MATERIAL_DESCRIPTION' in products_df.columns and 'MATERIAL_NUMBER' in products_df.columns:
            # On drop les doublons pour avoir des paires uniques
            unique_products = products_df[['MATERIAL_DESCRIPTION', 'MATERIAL_NUMBER']].drop_duplicates()
            desc_map = dict(zip(unique_products['MATERIAL_DESCRIPTION'], unique_products['MATERIAL_NUMBER']))
            
        # Nettoyage
        if 'AVERAGE_PRICE' in market_df.columns:
             market_df['AVERAGE_PRICE'] = pd.to_numeric(market_df['AVERAGE_PRICE'], errors='coerce').fillna(0)
             
        benchmarks = {}
        
        # Filtrer pour avoir les données du marché global
        if 'SALES_ORGANIZATION' in market_df.columns:
            market_only = market_df[market_df['SALES_ORGANIZATION'] == 'Market']
        else:
            market_only = market_df
            
        # Filtrer sur la dernière période de simulation dispo
        if 'SIMULATION_PERIOD' in market_only.columns:
            market_only['SIMULATION_PERIOD'] = pd.to_numeric(market_only['SIMULATION_PERIOD'], errors='coerce').fillna(0)
            max_period = market_only['SIMULATION_PERIOD'].max()
            if max_period > 0:
                market_only = market_only[market_only['SIMULATION_PERIOD'] == max_period]

        # Grouper par Description et Canal
        # Car Market n'a pas MATERIAL_NUMBER
        if 'MATERIAL_DESCRIPTION' not in market_only.columns:
            return {}

        grouped = market_only.groupby(['MATERIAL_DESCRIPTION', 'DISTRIBUTION_CHANNEL']).agg({
            'AVERAGE_PRICE': 'mean', 
        }).reset_index()
        
        for _, row in grouped.iterrows():
            desc = row['MATERIAL_DESCRIPTION']
            dc = row['DISTRIBUTION_CHANNEL']
            avg_price = row['AVERAGE_PRICE']
            
            # Retrouver le matériel number
            material = desc_map.get(desc)
            
            if material and avg_price > 0:
                if material not in benchmarks:
                    benchmarks[material] = {}
                benchmarks[material][dc] = round(avg_price, 2)
                
        return benchmarks

    def recommend_price_adjustments(self) -> pd.DataFrame:
        """
        Recommande des ajustements de prix basés sur le rapport ZMARKET
        Scénarios A (Prix < Marché), B (Prix > Marché), C (Prix = Marché)
        """
        # 1. Récupérer les données
        market_benchmarks = self.get_market_price_benchmarks()
        
        # Mes prix actuels
        my_prices_df = self.client.fetch_view("Current_Pricing_Conditions", top=1000)
        
        # Mes ventes (pour la vélocité)
        sales_df = self.client.fetch_view("Sales", top=10000)
        
        # Mon inventaire
        inventory_df = self.client.fetch_view("Current_Inventory", top=1000)
        
        recommendations = []
        
        # Liste des produits/canaux à analyser
        # On se base sur les prix définis actuellement
        if my_prices_df.empty:
            return pd.DataFrame()
            
        # Conversion types
        if 'PRICE' in my_prices_df.columns:
            my_prices_df['PRICE'] = pd.to_numeric(my_prices_df['PRICE'], errors='coerce').fillna(0)
            
        # Calcul Vélocité (Ventes par jour approx sur derniers jours)
        # On simplifie : Somme des ventes récentes
        sales_velocity = {}
        if not sales_df.empty:
            sales_df['QUANTITY'] = pd.to_numeric(sales_df['QUANTITY'], errors='coerce').fillna(0)
            # On pourrait filtrer sur les derniers jours si on avait la date, 
            # ici on prend tout le dataset dispo (souvent reset par round)
            sales_stats = sales_df.groupby(['MATERIAL_NUMBER', 'DISTRIBUTION_CHANNEL'])['QUANTITY'].sum().reset_index()
            for _, row in sales_stats.iterrows():
                k = (row['MATERIAL_NUMBER'], row['DISTRIBUTION_CHANNEL'])
                sales_velocity[k] = row['QUANTITY']

        # Calcul Stock
        stock_levels = {}
        if not inventory_df.empty:
            inventory_df['STOCK'] = pd.to_numeric(inventory_df['STOCK'], errors='coerce').fillna(0)
            inv_stats = inventory_df.groupby('MATERIAL_NUMBER')['STOCK'].sum()
            stock_levels = inv_stats.to_dict()

        for _, row in my_prices_df.iterrows():
            material = row['MATERIAL_NUMBER']
            dc = row['DISTRIBUTION_CHANNEL']
            my_price = float(row.get('PRICE', 0))
            
            # 1. Prix Marché
            market_price = 0
            if material in market_benchmarks and dc in market_benchmarks[material]:
                market_price = market_benchmarks[material][dc]
            
            if market_price == 0:
                continue # Pas de données marché
                
            # 2. Données contextuelles
            velocity = sales_velocity.get((material, dc), 0)
            stock = stock_levels.get(material, 0)
            
            gap = my_price - market_price
            gap_pct = (gap / market_price) * 100
            
            action = "MAINTAIN" 
            reason = "Aligné marché"
            new_price = my_price
            
            # Seuils
            HIGH_VELOCITY = 50 # Unités vendues (arbitraire, à ajuster)
            LOW_VELOCITY = 10
            HIGH_STOCK = 500
            
            # --- ALGORYTHME ZMARKET ---
            
            # Scénario A : Prix < Moyenne ZMARKET (ex: gap_pct < -2%)
            if gap_pct < -1.0: 
                situation = "Prix inférieur au marché"
                # "Si vos ventes sont très rapides et risque rupture -> Augmenter"
                if velocity > HIGH_VELOCITY or stock < 100:
                    action = "INCREASE"
                    reason = "Prix bas + Fortes ventes -> Augmenter marge"
                    new_price = (my_price + market_price) / 2 # On se rapproche de la moyenne
                else:
                    action = "MAINTAIN"
                    reason = "Prix bas mais ventes faibles/normales -> Gagner PDM"

            # Scénario B : Prix > Moyenne ZMARKET (ex: gap_pct > 2%)
            elif gap_pct > 1.0:
                situation = "Prix supérieur au marché"
                # "Si vous vendez bien -> Ne rien changer"
                if velocity > HIGH_VELOCITY:
                    action = "MAINTAIN"
                    reason = "Prix premium accepté par le marché"
                # "Si vous vendez peu -> Baisser"
                elif velocity < LOW_VELOCITY:
                    action = "DECREASE"
                    reason = "Prix trop élevé, ventes faibles -> S'aligner"
                    new_price = market_price * 0.99 # Légèrement sous le marché
                else:
                    action = "MONITOR"
                    reason = "Ventes moyennes à prix élevé"

            # Scénario C : Prix = Moyenne (à +/- 1%)
            else: 
                situation = "Aligné marché"
                # "Si beaucoup d'inventaire invendu -> Baisser"
                if stock > HIGH_STOCK and velocity < HIGH_VELOCITY:
                    action = "DECREASE"
                    reason = "Stock élevé -> Liquider"
                    new_price = market_price * 0.95
                else:
                    action = "MAINTAIN"
                    reason = "Aligné et stock correct"
            
            recommendations.append({
                'Produit': material,
                'Canal': dc,
                'Mon Prix': round(my_price, 2),
                'Prix Marché': round(market_price, 2),
                'Ecart': f"{gap_pct:+.1f}%",
                'Ventes': int(velocity),
                'Stock Global': int(stock),
                'Action': action,
                'Prix Conseillé': round(new_price, 2),
                'Raison': reason
            })
            
        df_reco = pd.DataFrame(recommendations)
        
        if not df_reco.empty:
            # Filtrer: Seulement produits avec ventes > 0
            df_reco = df_reco[df_reco['Ventes'] > 0]
            
            # Trier par Ventes (Décroissant) pour voir les Top Produits en premier
            df_reco = df_reco.sort_values('Ventes', ascending=False)
            
            # Garder le top 5
            df_reco = df_reco.head(5)
            
        return df_reco

    def recommend_prices(self, material_number: str) -> Dict[str, float]:
        """
        Recommande les prix optimaux par canal de distribution

        Args:
            material_number: Numero du produit

        Returns:
            Dict[dc] -> prix recommande
        """
        sales_df = self.client.fetch_view("Sales", top=10000)
        market_df = self.client.fetch_view("Market", top=10000)

        if sales_df.empty or market_df.empty:
            return {}

        # Conversion des types pour éviter les erreurs de calcul
        for col in ['NET_VALUE', 'QUANTITY', 'COST']:
            if col in sales_df.columns:
                sales_df[col] = pd.to_numeric(sales_df[col], errors='coerce').fillna(0)
        
        if 'NET_VALUE' in market_df.columns:
             market_df['NET_VALUE'] = pd.to_numeric(market_df['NET_VALUE'], errors='coerce').fillna(0)
        if 'QUANTITY' in market_df.columns:
             market_df['QUANTITY'] = pd.to_numeric(market_df['QUANTITY'], errors='coerce').fillna(0)

        # Filtrer par produit
        if 'MATERIAL_NUMBER' not in sales_df.columns or 'MATERIAL_NUMBER' not in market_df.columns:
            logger.warning(f"Colonne MATERIAL_NUMBER manquante. Sales cols: {sales_df.columns}, Market cols: {market_df.columns}")
            return {}

        product_sales = sales_df[sales_df['MATERIAL_NUMBER'] == material_number]
        market_data = market_df[market_df['MATERIAL_NUMBER'] == material_number]

        recommendations = {}

        for dc in ['10', '12', '14']:
            # Récupérer les ventes actuelles de ce DC
            dc_sales = product_sales[product_sales['DISTRIBUTION_CHANNEL'] == dc]

            # Récupérer prix moyen marche
            market_prices = market_data[market_data['DISTRIBUTION_CHANNEL'] == dc]

            if not dc_sales.empty and not market_prices.empty:
                avg_sold_price = (dc_sales['NET_VALUE'].sum() / 
                                dc_sales['QUANTITY'].sum()) if dc_sales['QUANTITY'].sum() > 0 else 0
                market_avg_price = market_prices['NET_VALUE'].values[0] / market_prices['QUANTITY'].values[0] if market_prices['QUANTITY'].values[0] > 0 else 0

                # Élasticité par DC
                elasticities = {'10': -4.0, '12': -2.5, '14': -1.5}
                elasticity = elasticities.get(dc, -2.5)

                # Formule simple: ajuster le prix selon la part de marche
                market_share = dc_sales['QUANTITY'].sum() / market_prices['QUANTITY'].sum()

                if market_share < 0.3:  # Part basse
                    recommended = avg_sold_price * 1.05
                elif market_share > 0.5:  # Part haute
                    recommended = avg_sold_price * 0.98
                else:
                    recommended = avg_sold_price

                recommendations[f"DC{dc}"] = round(recommended, 2)

        return recommendations

    def recommend_zones(self, material_number: str) -> Dict[str, float]:
        """
        Recommande les zones prioritaires

        Args:
            material_number: Numero du produit

        Returns:
            Dict[zone] -> score priorite
        """
        sales_df = self.client.fetch_view("Sales", top=10000)
        market_df = self.client.fetch_view("Market", top=10000)

        if sales_df.empty or market_df.empty:
            return {}

        # Conversion des types
        for col in ['NET_VALUE', 'QUANTITY', 'COST']:
            if col in sales_df.columns:
                sales_df[col] = pd.to_numeric(sales_df[col], errors='coerce').fillna(0)

        if 'NET_VALUE' in market_df.columns:
             market_df['NET_VALUE'] = pd.to_numeric(market_df['NET_VALUE'], errors='coerce').fillna(0)
        if 'QUANTITY' in market_df.columns:
             market_df['QUANTITY'] = pd.to_numeric(market_df['QUANTITY'], errors='coerce').fillna(0)

        product_sales = sales_df[sales_df['MATERIAL_NUMBER'] == material_number]
        market_data = market_df[market_df['MATERIAL_NUMBER'] == material_number]

        scores = {}

        for zone in ['North', 'South', 'West']:
            zone_sales = product_sales[product_sales['AREA'] == zone]
            zone_market = market_data[market_data['AREA'] == zone]

            if not zone_sales.empty and not zone_market.empty:
                our_qty = zone_sales['QUANTITY'].sum()
                market_qty = zone_market['QUANTITY'].sum()

                market_share = our_qty / market_qty if market_qty > 0 else 0

                # Score = potentiel non exploite
                potential_score = (1 - market_share) * market_qty

                scores[zone] = round(potential_score, 0)

        return scores

    def recommend_product_portfolio(self) -> Dict[str, float]:
        """
        Recommande le portfolio de produits optimal

        Returns:
            Dict[material] -> part recommandee (%)
        """
        sales_df = self.client.fetch_view("Sales", top=10000)

        if sales_df.empty:
            return {}

        # Conversion des types
        for col in ['QUANTITY', 'NET_VALUE', 'COST']:
            if col in sales_df.columns:
                sales_df[col] = pd.to_numeric(sales_df[col], errors='coerce').fillna(0)

        # Calculer la marge et velocite par produit
        product_stats = sales_df.groupby('MATERIAL_NUMBER').agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()

        product_stats['PROFIT'] = product_stats['NET_VALUE'] - product_stats['COST']
        product_stats['MARGIN_PCT'] = (product_stats['PROFIT'] / 
                                       product_stats['NET_VALUE'] * 100)

        # Normaliser pour avoir un score
        total_qty = product_stats['QUANTITY'].sum()
        product_stats['SCORE'] = (product_stats['MARGIN_PCT'] * 
                                 product_stats['QUANTITY'] / total_qty)

        # Recommandation: focus sur top 6-8 produits
        top_products = product_stats.nlargest(6, 'SCORE')

        recommendations = {}
        total_score = top_products['SCORE'].sum()

        for idx, row in top_products.iterrows():
            pct = (row['SCORE'] / total_score * 100)
            recommendations[row['MATERIAL_NUMBER']] = round(pct, 1)

        return recommendations

    def analyze_price_elasticity(self, material_number: str) -> pd.DataFrame:
        """
        Analyse l'élasticité prix pour un produit donné
        
        Args:
            material_number: Code produit (ex: F13)
            
        Returns:
            DataFrame avec colonnes: UNIT_PRICE, QUANTITY, NET_VALUE, COST, MARGIN
        """
        sales_df = self.client.fetch_view("Sales", top=10000)
        
        if sales_df.empty:
            return pd.DataFrame()
            
        # Filtrer et nettoyer
        if 'NET_VALUE' in sales_df.columns:
            sales_df['NET_VALUE'] = pd.to_numeric(sales_df['NET_VALUE'], errors='coerce').fillna(0)
        if 'QUANTITY' in sales_df.columns:
            sales_df['QUANTITY'] = pd.to_numeric(sales_df['QUANTITY'], errors='coerce').fillna(0)
        if 'COST' in sales_df.columns:
            sales_df['COST'] = pd.to_numeric(sales_df['COST'], errors='coerce').fillna(0)
            
        # Filtrer par produit
        # Essayer avec MATERIAL_NUMBER ou DESCRIPTION
        product_sales = sales_df[sales_df['MATERIAL_NUMBER'] == material_number].copy()
        
        if product_sales.empty:
            return pd.DataFrame()
            
        # Calculer prix unitaire moyen pour chaque transaction
        # On assume NET_VALUE = Prix * Qty. Si Qty=0, Prix=0
        product_sales['UNIT_PRICE'] = product_sales.apply(
            lambda x: (x['NET_VALUE'] / x['QUANTITY']) if x['QUANTITY'] > 0 else 0, axis=1
        ).round(2)
        
        # Grouper par prix unitaires similaires 
        analysis = product_sales.groupby('UNIT_PRICE').agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()
        
        analysis['MARGIN'] = analysis['NET_VALUE'] - analysis['COST']
        analysis = analysis.sort_values('UNIT_PRICE')
        
        return analysis

    def predict_revenue(self, current_price: float, elasticity: float = -2.5, base_qty: int = 1000) -> pd.DataFrame:
        """
        Simule le revenu pour différentes variations de prix
        Basé sur une élasticité simple: % Chg Qty = Elasticity * % Chg Price
        """
        # Scénarios: -20% à +20%
        price_factors = [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]
        
        rows = []
        for factor in price_factors:
            new_price = current_price * factor
            pct_change_price = factor - 1.0
            
            # Formule élasticité: %Q = E * %P
            pct_change_qty = elasticity * pct_change_price
            new_qty = base_qty * (1 + pct_change_qty)
            
            # Ne pas avoir de quantité négative
            new_qty = max(0, new_qty)
            
            projected_revenue = new_price * new_qty
            
            rows.append({
                'Variation Prix': f"{pct_change_price*100:+.0f}%",
                'Nouveau Prix': new_price,
                'Qté Prévue': int(new_qty),
                'Revenu Projeté': projected_revenue
            })
            
        return pd.DataFrame(rows)

    def recommend_marketing_strategy(self) -> pd.DataFrame:
        """
        Génère la table de stratégie marketing basée sur la taille et la région.
        Règles spécifiées par l'utilisateur:
        - 500g (F04, F05): Investir massivement (sensibilité haute).
        - 1kg (F11, F12, F13): Budget faible (sensibilité basse).
        - Régions: Ouest (F04, F13), Nord (F05, F11/F12), Sud (F04, F11/F12/F13).
        - Stock: Si stock = 0 -> Marketing = 0.
        """
        # 1. Identifier les produits actifs
        active_products = self.get_active_products()
        if not active_products:
            return pd.DataFrame()
        
        # 2. Récupérer l'inventaire actuel pour check de rupture
        inventory_df = self.client.fetch_view("Current_Inventory", top=1000)
        stock_map = {}
        if not inventory_df.empty:
            if 'STOCK' in inventory_df.columns: inventory_df['STOCK'] = pd.to_numeric(inventory_df['STOCK'], errors='coerce').fillna(0)
            stock_map = inventory_df.groupby('MATERIAL_NUMBER')['STOCK'].sum().to_dict()
            
        # 3. Récupérer les descriptions
        sales_summary = self.analyzer.get_sales_summary()
        desc_map = {}
        if not sales_summary.empty:
            desc_map = dict(zip(sales_summary['MATERIAL_NUMBER'], sales_summary['MATERIAL_DESCRIPTION']))
            
        rows = []
        
        north_1kg_candidates = [] # Pour gérer la cannibalisation (F11 vs F12)
        
        for product in active_products:
            stock = stock_map.get(product, 0)
            desc = desc_map.get(product, "")
            
            # --- Logique Taille ---
            is_500g = "500g" in desc or product in ["F04", "F05"]
            is_1kg = "1kg" in desc or product in ["F11", "F12", "F13"]
            
            # --- Stratégie par Région ---
            strat_north = ""
            strat_south = ""
            strat_west = ""
            note = ""
            
            # F04 Raisin
            if "F04" in product or ("Raisin" in desc and is_500g):
                strat_west = "+++ (Priorité)"
                strat_south = "++ (Moyen)"
                note = "Star de l'Ouest (500g). Investir massivement."

            # F05 Original
            elif "F05" in product or ("Original" in desc and is_500g):
                strat_north = "+++ (Priorité)"
                note = "Star du Nord (500g). Investir massivement."

            # F11 Noix
            elif "F11" in product or ("Nut" in desc and is_1kg) or ("Noix" in desc and is_1kg):
                strat_north = "+ (Alterner)"
                strat_south = "+ (Maintien)"
                note = "1kg (Sensibilité faible). Attention cannibalisation Nord."
                north_1kg_candidates.append(product)

            # F12 Bleuet
            elif "F12" in product or ("Blueberry" in desc and is_1kg) or ("Bleuet" in desc and is_1kg):
                strat_north = "+ (Alterner)"
                strat_south = "+ (Maintien)"
                note = "1kg (Sensibilité faible). Maintien uniquement."
                north_1kg_candidates.append(product)

            # F13 Fraise
            elif "F13" in product or ("Strawberry" in desc and is_1kg) or ("Fraise" in desc and is_1kg):
                strat_west = "++ (Moyen)"
                strat_south = "+ (Maintien)"
                note = "Complément Ouest (1kg)."
            
            # --- Check Rupture ---
            if stock == 0:
                strat_north = "⛔ STOP (0 Stock)"
                strat_south = "⛔ STOP (0 Stock)"
                strat_west = "⛔ STOP (0 Stock)"
                note = "Rupture de stock. Couper tout marketing."
                
            rows.append({
                "Produit": f"{product} - {desc}",
                "NORD": strat_north,
                "SUD": strat_south,
                "OUEST": strat_west,
                "Note Stratégique": note,
                "_code": product,
                "_stock": stock
            })
            
        df = pd.DataFrame(rows)
        
        # --- Gestion Cannibalisation Nord (F11 vs F12) ---
        # "Alternez. Faites de la pub pour celui dont vous avez le plus de stock"
        if len(north_1kg_candidates) >= 2:
            # Identifier le leader de stock
            candidates_data = [r for r in rows if r['_code'] in north_1kg_candidates]
            # Trier par stock decroissant
            candidates_data.sort(key=lambda x: x['_stock'], reverse=True)
            
            leader = candidates_data[0]
            others = candidates_data[1:]
            
            # Mettre à jour le DF
            for i, row in df.iterrows():
                if row['_code'] == leader['_code']:
                     if "STOP" not in df.at[i, 'NORD']:
                        df.at[i, 'NORD'] = "++ (Focus Stock)"
                        df.at[i, 'Note Stratégique'] += " Leader stock 1kg Nord."
                elif row['_code'] in [o['_code'] for o in others]:
                     if "STOP" not in df.at[i, 'NORD']:
                        df.at[i, 'NORD'] = "PAUSE (Cannib.)"
                        df.at[i, 'Note Stratégique'] += " En pause pour éviter cannibalisation."

        if not df.empty:
            df = df.drop(columns=['_code', '_stock'])
            
        return df
