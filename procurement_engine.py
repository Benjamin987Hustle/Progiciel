"""
Moteur de décision pour l'approvisionnement
"""

import pandas as pd
from typing import Dict, List, Tuple
from odata_client import ODataClient
import logging

logger = logging.getLogger(__name__)


class ProcurementEngine:
    """Moteur de décision pour l'approvisionnement"""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.client = ODataClient()

    def check_reorder_needed(self) -> Dict[str, Dict]:
        """
        Vérifie quels matériaux necessitent une commande

        Returns:
            Dict[material] -> {status, days_remaining, urgency}
        """
        inventory_df = self.client.fetch_view("Current_Inventory", top=10000)
        sales_df = self.client.fetch_view("Sales", top=10000)

        if inventory_df.empty or sales_df.empty:
            return {}

        # Calculer la consommation quotidienne par matériau
        material_consumption = {}

        for idx, sale in sales_df.iterrows():
            material = sale.get('MATERIAL_NUMBER')
            try:
                qty = float(sale.get('QUANTITY', 0))
            except (ValueError, TypeError):
                qty = 0.0

            if material not in material_consumption:
                material_consumption[material] = 0

            material_consumption[material] += qty

        # Nombre de ventes (comme proxy pour les jours)
        num_periods = len(sales_df['SIM_STEP'].unique())
        daily_consumption = {m: q / max(num_periods, 1) 
                           for m, q in material_consumption.items()}

        # Analyser par matériau d'inventaire
        reorder_recommendations = {}

        for idx, inv in inventory_df.iterrows():
            material = inv.get('MATERIAL_NUMBER')
            try:
                stock = float(inv.get('STOCK', 0))
            except (ValueError, TypeError):
                stock = 0.0
                
            try:
                restricted = float(inv.get('RESTRICTED', 0))
            except (ValueError, TypeError):
                restricted = 0.0
                
            available = stock - restricted

            if material in daily_consumption:
                daily_use = daily_consumption[material]

                if daily_use > 0:
                    days_remaining = available / daily_use
                else:
                    days_remaining = 999

                # Déterminer l'urgence
                if days_remaining <= 3:
                    urgency = "CRITICAL"
                    status = "COMMANDER IMMEDIATEMENT"
                elif days_remaining <= 7:
                    urgency = "HIGH"
                    status = "COMMANDER BIENTOT"
                elif days_remaining <= 14:
                    urgency = "MEDIUM"
                    status = "Planifier une commande"
                else:
                    urgency = "LOW"
                    status = "Stock suffisant"

                reorder_recommendations[material] = {
                    'status': status,
                    'days_remaining': round(days_remaining, 1),
                    'urgency': urgency,
                    'stock_available': available,
                    'daily_consumption': round(daily_use, 1)
                }

        return reorder_recommendations

    def calculate_mrp_needs(self) -> Dict[str, float]:
        """
        Calcule les besoins de matieres premieres (MRP)

        Returns:
            Dict[material] -> quantite a commander
        """
        sales_forecast = self.client.fetch_view("Independent_Requirements", top=10000)
        inventory = self.client.fetch_view("Current_Inventory", top=10000)

        if sales_forecast.empty:
            return {}

        # Agreger les besoins
        needed = {}

        for idx, req in sales_forecast.iterrows():
            material = req.get('MATERIAL_NUMBER')
            try:
                qty = float(req.get('QUANTITY', 0))
            except (ValueError, TypeError):
                qty = 0.0

            if material not in needed:
                needed[material] = 0

            needed[material] += qty

        # Soustraire le stock disponible
        recommendations = {}

        for material, qty_needed in needed.items():
            # Trouver le stock actuel
            current_stock = 0

            if not inventory.empty:
                mat_inv = inventory[inventory['MATERIAL_NUMBER'] == material]
                if not mat_inv.empty:
                    try:
                        current_stock = float(mat_inv.iloc[0].get('STOCK', 0))
                    except (ValueError, TypeError):
                        current_stock = 0.0

            to_order = max(0, qty_needed - current_stock)

            if to_order > 0:
                recommendations[material] = to_order

        return recommendations

    def get_purchase_order_status(self) -> pd.DataFrame:
        """
        Récupère le statut des commandes en cours

        Returns:
            DataFrame avec les commandes
        """
        purchase_orders = self.client.fetch_view("Purchase_Orders", top=10000)

        if purchase_orders.empty:
            return purchase_orders

        # Filtrer par statut
        in_progress = purchase_orders[purchase_orders['STATUS'] != 'Delivered']

        return in_progress
