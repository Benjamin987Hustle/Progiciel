"""
Moteur de décision financier
"""

import pandas as pd
from typing import Dict, Tuple
from odata_client import ODataClient
import logging

logger = logging.getLogger(__name__)


class FinanceEngine:
    """Moteur de décision financier"""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.client = ODataClient()

    def analyze_cash_position(self) -> Dict:
        """
        Analyse la position financière

        Returns:
            Dict avec metriques financieres
        """
        valuation_df = self.client.fetch_view("Company_Valuation", top=10000)

        if valuation_df.empty:
            return {}

        latest = valuation_df.iloc[-1]

        cash = float(latest.get('BANK_CASH_ACCOUNT', 0))
        loan = float(latest.get('BANK_LOAN', 0))
        receivables = float(latest.get('ACCOUNTS_RECEIVABLE', 0))
        payables = float(latest.get('ACCOUNTS_PAYABLE', 0))
        profit = float(latest.get('PROFIT', 0))
        credit_rating = latest.get('CREDIT_RATING', 'Unknown')

        net_debt = (loan + payables) - (cash + receivables)

        analysis = {
            'cash': cash,
            'loan': loan,
            'receivables': receivables,
            'payables': payables,
            'net_debt': net_debt,
            'profit': profit,
            'credit_rating': credit_rating,
            'working_capital': cash + receivables - payables
        }

        return analysis

    def get_debt_payoff_recommendation(self) -> Dict:
        """
        Recommande si et comment payer la dette

        Returns:
            Dict avec recommendations
        """
        analysis = self.analyze_cash_position()

        if not analysis:
            return {}

        cash = analysis['cash']
        loan = analysis['loan']
        net_debt = analysis['net_debt']
        credit_rating = analysis['credit_rating']

        # Seuils par rating
        rating_thresholds = {
            'AAA+': 1_000_000,
            'AA+': 2_000_000,
            'A': 5_000_000,
            'BBB': 8_000_000,
            'B': 14_000_000
        }

        target_debt = rating_thresholds.get(credit_rating, 5_000_000)

        recommendation = {
            'current_net_debt': net_debt,
            'target_net_debt': target_debt,
            'available_cash': cash,
            'current_rating': credit_rating,
            'can_improve_rating': net_debt > target_debt
        }

        if net_debt > target_debt and cash > 1_000_000:
            # Recommander le paiement
            amount_to_pay = min(net_debt - target_debt, cash - 500_000)

            recommendation['action'] = 'PAYER DETTE'
            recommendation['amount_to_pay'] = amount_to_pay
            recommendation['reason'] = f"Reduire le net debt de €{net_debt:,.0f} a €{target_debt:,.0f}"

        elif cash < 500_000:
            recommendation['action'] = 'CONSERVER CASH'
            recommendation['reason'] = 'Liquidite insuffisante'

        else:
            recommendation['action'] = 'OPTIONNEL'
            recommendation['reason'] = 'Position confortable'

        return recommendation

    def get_profitability_by_product(self) -> pd.DataFrame:
        """
        Analyse la profitabilité par produit

        Returns:
            DataFrame avec rentabilité
        """
        sales_df = self.client.fetch_view("Sales", top=10000)

        if sales_df.empty:
            return sales_df

        # Convertir types
        for col in ['QUANTITY', 'NET_VALUE', 'COST']:
            if col in sales_df.columns:
                sales_df[col] = pd.to_numeric(sales_df[col], errors='coerce')

        # Agreger par produit
        # On inclut MATERIAL_NUMBER s'il existe
        group_cols = ['MATERIAL_DESCRIPTION']
        if 'MATERIAL_NUMBER' in sales_df.columns:
            group_cols.insert(0, 'MATERIAL_NUMBER')
            
        profitability = sales_df.groupby(group_cols).agg({
            'QUANTITY': 'sum',
            'NET_VALUE': 'sum',
            'COST': 'sum'
        }).reset_index()

        profitability['PROFIT'] = profitability['NET_VALUE'] - profitability['COST']
        profitability['AVG_PRICE'] = profitability['NET_VALUE'] / profitability['QUANTITY']
        profitability['UNIT_COST'] = profitability['COST'] / profitability['QUANTITY']
        profitability['UNIT_PROFIT'] = profitability['PROFIT'] / profitability['QUANTITY']
        profitability['MARGIN_PCT'] = (profitability['PROFIT'] / 
                                       profitability['NET_VALUE'] * 100).round(2)

        return profitability.sort_values('PROFIT', ascending=False)

    def get_roi_marketing(self) -> pd.DataFrame:
        """
        Calcule le ROI des dépenses marketing

        Returns:
            DataFrame avec ROI
        """
        marketing_df = self.client.fetch_view("Marketing_Expenses", top=10000)
        sales_df = self.client.fetch_view("Sales", top=10000)

        if marketing_df.empty or sales_df.empty:
            return pd.DataFrame()

        # TODO: Implémenter le calcul complet du ROI
        # Pour l'instant, retourner un résumé

        marketing_summary = marketing_df.groupby('MATERIAL_DESCRIPTION').agg({
            'AMOUNT': 'sum'
        }).reset_index()

    def calculate_valuation_impact(self, current_profit: float, current_net_debt: float) -> Dict:
        """
        Calcule l'impact de la dette sur la valorisation
        Basé sur la formule : Valorisation = Profit / Taux d'actualisation
        Taux : 
        - AAA+ (Dette < 1M) : 10%
        - AA+ (Dette < 2M) : 10.5%
        - A   (Dette < 5M) : 12%
        - BBB (Dette < 8M) : 15%
        - B   (Dette > 8M) : 20%
        """
        # 1. Déterminer le rating actuel (approximatif basé sur la dette)
        # Note: Le rating dépend aussi d'autres facteurs, mais la dette est majeure.
        
        def get_discount_rate(debt):
            if debt <= 1_000_000: return 0.10  # AAA+
            if debt <= 2_000_000: return 0.105 # AA+
            if debt <= 5_000_000: return 0.12  # A
            if debt <= 8_000_000: return 0.15  # BBB
            return 0.20                        # B
            
        current_rate = get_discount_rate(current_net_debt)
        target_rate = 0.10 # Objectif AAA+
        
        current_valuation = current_profit / current_rate if current_rate > 0 else 0
        potential_valuation = current_profit / target_rate
        
        impact = potential_valuation - current_valuation
        
        return {
            'current_rate': current_rate,
            'target_rate': target_rate,
            'current_valuation': current_valuation,
            'potential_valuation': potential_valuation,
            'impact_value': impact,
            'is_optimized': current_rate == target_rate
        }

    def calculate_stock_costs(self) -> Dict:
        """
        Calcule les coûts de stockage et l'immobilisation financière
        Seuil critique : 250,000 unités
        Coût dépassement : 500€/jour par 50k unités
        Coût standard moyen : ~1.38€ (pour valoriser le cash trap)
        """
        inventory_df = self.client.fetch_view("Current_Inventory", top=10000)
        
        if inventory_df.empty:
             return {}
             
        if 'STOCK' in inventory_df.columns:
            inventory_df['STOCK'] = pd.to_numeric(inventory_df['STOCK'], errors='coerce').fillna(0)
            
        total_units = inventory_df['STOCK'].sum()
        
        # Coût cash trap (argent qui dort)
        # Estimation : 1.38€ par unité (Muesli standard)
        cash_trap = total_units * 1.38
        
        # Frais de stockage (Estimes - ERPsim Rules)
        # Gratuit jusqu'a 250k
        storage_fees = 0
        if total_units > 250_000:
            excess = total_units - 250_000
            # 500 EUR par tranche de 50k
            tranches = (excess // 50_000) + 1
            storage_fees = tranches * 500
            
        return {
            'total_units': int(total_units),
            'cash_trap': cash_trap,
            'storage_fees_daily': storage_fees,
            'is_critical': total_units > 250_000
        }

    def calculate_setup_roi(self, daily_changeovers: int = 1) -> Dict:
        """
        Calcule le ROI de la réduction du temps de setup.
        Hypothèse: 
        - Gain = 1h de prod par setup réduit
        - Capacité = 24h * 1000 (exemple) -> 1h = ~1000 unités ??
        (A ajuster selon simulation)
        User data:
        - 1h de gagnée = 16,000 / 24 = 666 unités
        - Marge unitaire ~ 1.50€
        - Gain par jour = 666 * 1.5 * nbr_changement
        - Coût investissement = 50,000€
        """
        
        units_per_hour = 666
        margin_per_unit = 1.50
        
        gain_per_setup = units_per_hour * margin_per_unit # ~1000€
        daily_gain = gain_per_setup * daily_changeovers
        
        investment_cost = 50_000
        days_to_roi = investment_cost / daily_gain if daily_gain > 0 else 999
        
        return {
            'gain_per_setup': gain_per_setup,
            'daily_gain': daily_gain,
            'investment_cost': investment_cost,
            'days_to_roi': round(days_to_roi, 1),
            'recommendation': "INVESTIR" if days_to_roi < 15 else "ATTENDRE"
        }
