import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from sales_engine import SalesEngine

class TestPricing(unittest.TestCase):
    @patch('sales_engine.ODataClient')
    def test_zmarket_scenarios(self, MockClient):
        # Setup Mock
        client_instance = MockClient.return_value
        analyzer_mock = MagicMock()
        engine = SalesEngine(analyzer_mock)
        engine.client = client_instance # Force replace

        # 1. Mock Market Data (ZMARKET)
        market_data = pd.DataFrame({
            'MATERIAL_DESCRIPTION': [f'Desc P{i}' for i in range(1, 10)],
            'DISTRIBUTION_CHANNEL': ['10'] * 9,
            'SALES_ORGANIZATION': ['Market'] * 9,
            'AVERAGE_PRICE': [100.0] * 9,
            'QUANTITY': [1000] * 9,
            'SIMULATION_PERIOD': [1] * 9
        })

        # 2. Mock My Prices (VK32)
        my_prices = pd.DataFrame({
            'MATERIAL_NUMBER': [f'P{i}' for i in range(1, 10)],
            'MATERIAL_DESCRIPTION': [f'Desc P{i}' for i in range(1, 10)],
            'DISTRIBUTION_CHANNEL': ['10'] * 9,
            'PRICE': [100.0] * 9 # Aligned prices
        })

        # 3. Mock Inventory
        inventory = pd.DataFrame({
            'MATERIAL_NUMBER': [f'P{i}' for i in range(1, 10)],
            'STOCK': [100] * 9,
            'RESTRICTED': [0] * 9
        })

        # 4. Mock Sales (Velocity)
        # 6 items with sales, 3 without
        # P1=60, P2=50, P3=40, P4=30, P5=20, P6=10, P7=0, P8=0, P9=0
        sales_data = []
        for i, qty in enumerate([60, 50, 40, 30, 20, 10, 0, 0, 0], 1):
             if qty > 0:
                 sales_data.append({'MATERIAL_NUMBER': f'P{i}', 'DISTRIBUTION_CHANNEL': '10', 'QUANTITY': qty})
        
        sales = pd.DataFrame(sales_data) if sales_data else pd.DataFrame(columns=['MATERIAL_NUMBER', 'DISTRIBUTION_CHANNEL', 'QUANTITY'])

        # 5. Game Rules
        game_rules = pd.DataFrame({'SIMULATION_PERIOD': [1]})

        # Configure side_effect for fetch_view
        def side_effect(view_name, top=None):
            if view_name == "Market": return market_data
            if view_name == "Current_Pricing_Conditions": return my_prices
            if view_name == "Current_Inventory": return inventory
            if view_name == "Sales": return sales
            if view_name == "Current_Game_Rules": return game_rules
            return pd.DataFrame()

        client_instance.fetch_view.side_effect = side_effect

        # Run Logic
        recommendations = engine.recommend_price_adjustments()

        print("\n--- RECOMMANDATIONS ZMARKET (TOP 5 TEST) ---\n")
        if not recommendations.empty:
            print(recommendations.to_string())
        else:
            print("No recommendations generated.")

        # Assertions
        # Should have exactly 5 rows
        self.assertEqual(len(recommendations), 5)
        
        # Should be sorted by Ventes descending
        # P1 (60), P2 (50), P3 (40), P4 (30), P5 (20) use 'Ventes' column
        expected_sales = [60, 50, 40, 30, 20]
        self.assertEqual(recommendations['Ventes'].tolist(), expected_sales)
        
        # P6 (10 sales) should be excluded because only top 5
        self.assertNotIn('P6', recommendations['Produit'].values)
        
        # P7 (0 sales) should be excluded
        self.assertNotIn('P7', recommendations['Produit'].values)

if __name__ == '__main__':
    unittest.main()
