# Système de Gestion ERPsim Manufacturing

Un système complet en Python pour analyser et optimiser votre simulation ERPsim Manufacturing.

## Architecture

```
erpsim_system/
├── config.py              # Configuration + connexion OData
├── odata_client.py        # Client OData pour récupérer les données
├── schemas.py             # Modèles Pydantic pour validation
├── analyzer.py            # Analyseur principal de données
├── sales_engine.py        # Moteur de décision VENTES
├── procurement_engine.py  # Moteur de décision APPROVISIONNEMENT
├── finance_engine.py      # Moteur de décision FINANCE
├── main.py                # Point d'entrée + menu interactif
└── requirements.txt       # Dépendances Python
```

## Installation

### 1. Créez le fichier `.env`

```bash
cp .env.example .env
```

Puis éditez `.env` avec vos paramètres:

```
ODATA_BASE_URL=https://sapvm2.hec.ca:8001/odata/300
ODATA_USERNAME=H_5
ODATA_PASSWORD=Canada
COMPANY_CODE=H2
PLANT=1000
```

### 2. Installez les dépendances

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Fonctionnalités

### 1. **Analyse Générale** (`analyzer.py`)
- ✅ Récupération données OData
- ✅ Ventes par produit, zone, canal
- ✅ Inventaire en temps réel
- ✅ Ordres production/achat
- ✅ Valorisation entreprise

### 2. **Moteur Ventes** (`sales_engine.py`)
Répond à:
- **Où vendre?** → Zones prioritaires par produit
- **À qui vendre?** → Canaux optimaux (DC10/12/14)
- **Quel produit?** → Portfolio optimal
- **Quel prix?** → Prix recommandés par DC

### 3. **Moteur Approvisionnement** (`procurement_engine.py`)
Répond à:
- **Commander?** → Seuils de réapprovisionnement
- **Quoi commander?** → Calcul MRP
- **Quand?** → Tracking des PO en cours

### 4. **Moteur Finance** (`finance_engine.py`)
Répond à:
- **Payer dette?** → Analyse cash + recommandation
- **Rentabilité?** → Par produit/canal
- **ROI Marketing?** → Allocation budget optimal

## Menu Interactif

Après le lancement, choisissez:

```
1. Afficher le résumé complet
2. Analyser ventes par produit
3. Analyser ventes par zone
4. Analyser ventes par canal (DC10/12/14)
5. Voir inventaire détaillé
6. Voir ordres production
7. Voir commandes achat
8. Exporter en Excel
9. Rafraîchir les données
0. Quitter
```

## Exemple d'Utilisation

### Vous voulez savoir vos top produits:

```python
from analyzer import ERPSimAnalyzer

analyzer = ERPSimAnalyzer()
df = analyzer.get_sales_summary()
print(df.head())
```

### Vous voulez les recommandations de prix:

```python
from sales_engine import SalesEngine

engine = SalesEngine(analyzer)
prices = engine.recommend_prices('HH-F13')  # Strawberry Muesli 1kg
print(prices)  # {'DC10': 5.42, 'DC12': 5.15, 'DC14': 5.78}
```

### Vous voulez vérifier les stocks critiques:

```python
from procurement_engine import ProcurementEngine

procurement = ProcurementEngine(analyzer)
reorders = procurement.check_reorder_needed()

for material, rec in reorders.items():
    if rec['urgency'] == 'CRITICAL':
        print(f"⚠️  {material}: {rec['status']}")
```

### Vous voulez analyser les finances:

```python
from finance_engine import FinanceEngine

finance = FinanceEngine(analyzer)
analysis = finance.analyze_cash_position()
print(f"Cash: €{analysis['cash']:,.0f}")
print(f"Loan: €{analysis['loan']:,.0f}")
print(f"Rating: {analysis['credit_rating']}")

recommendation = finance.get_debt_payoff_recommendation()
print(f"Action: {recommendation['action']}")
```

## Structure OData Disponible

Le système utilise ces vues OData:

1. **Sales** - Ventes détaillées (17 colonnes)
2. **Market** - Données marché agrégées
3. **Current_Inventory** - Stock temps réel
4. **Current_Inventory_KPI** - KPIs inventaire
5. **Purchase_Orders** - Commandes fournisseurs
6. **Production_Orders** - Ordres production
7. **Pricing_Conditions** - Prix de vente
8. **Current_Suppliers_Prices** - Prix d'achat
9. **Marketing_Expenses** - Budget marketing
10. **Financial_Postings** - Comptabilité
11. **Company_Valuation** - Valorisation
12. **BOM_Changes** - Changes nomenclature
13. **Carbon_Emissions** - Emissions CO2
14. **Independent_Requirements** - Prévisions
15. **Production** - Production détaillée
16. **Stock_Transfers** - Mouvements stocks
17. **Current_Game_Rules** - Règles simulation

## Points Clés d'Optimisation

### Ventes
- Focus sur **Top 6-8 produits** (80% du profit)
- Adapter prix par **canal** (DC10: -5%, DC12: 0%, DC14: +15%)
- Prioriser zones à faible **market share** (<30%)

### Approvisionnement
- **Seuil critique**: < 3 jours stock
- **Seuil urgent**: < 7 jours stock
- Regrouper commandes par **fournisseur**

### Finance
- Maintenir **cash > €500k** (flexibilité)
- Cibler **net debt < €5M** (rating A+)
- Payer dette quand **cash > €2M**

### Marketing
- **ROI minimum**: 3:1 requis
- Ne pas cannibaliser: 1 produit/zone
- Arrêter si stock < 2 jours

## Export Excel

Le menu génère un fichier Excel avec:
- Résumé valorisation
- Ventes par produit
- Ventes par zone/canal
- Inventaire détaillé
- Ordres production
- Commandes achat

Fichier: `erpsim_report_H2.xlsx`

## Troubleshooting

### Erreur 401/403
→ Vérifiez les identifiants dans `.env`

### Erreur 404
→ Vérifiez l'URL OData

### Empty DataFrame
→ Vérifiez que la simulation est ouverte

### Slow loading
→ Réduisez `top` dans `fetch_view()` (ex: top=1000)

## Prochaines Phases

- [ ] Dashboard Streamlit temps réel
- [ ] Prévisions ML (Prophet)
- [ ] Optimisation prix automatique
- [ ] Allocation marketing IA
- [ ] Alertes intelligentes
- [ ] Recommandations stratégiques
