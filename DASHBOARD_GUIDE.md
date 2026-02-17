# 📊 Tableau de Bord ERPsim - Guide d'Utilisation

## Lancement

```bash
streamlit run dashboard.py
```

L'application s'ouvre à: `http://localhost:8501`

## Structure du Dashboard

### 🏠 Accueil
- **KPIs Principaux:** Vue instantanée des 5 chiffres clés
  - Company Valuation
  - Cash disponible
  - Loan (crédit)
  - Profit net
  - Credit Rating

### 📈 Tab 1: VENTES
Analyse complète de vos ventes:

**Top Produits par Revenus**
- Classement des 8 meilleurs produits
- Visualisation des marges
- Tableau détaillé avec quantités

**Ventes par Zone**
- Répartition North/South/West
- Graphique en camembert
- Marges par zone

**Ventes par Canal**
- Analyse DC10 (Hypermarkets): volumetrie mais marge basse
- Analyse DC12 (Grocery): équilibré, meilleur volume
- Analyse DC14 (Convenience): meilleure marge

**Insights:**
- DC12 = 65% du chiffre (recommandé)
- DC14 = meilleure marge (75.6%)
- Focus: amplifier DC12 + marge de DC14

---

### 📦 Tab 2: APPROVISIONNEMENT
Gestion des stocks et commandes:

**Matériaux Critiques**
- 🔴 CRITIQUE: < 3 jours de stock
- 🟠 URGENT: 3-7 jours de stock
- Actions recommandées

**Inventaire Produits Finis**
- Total en stock (unités)
- Nombre de SKUs
- Top produits en stock

**Ordres de Production**
- Visualisation cible vs confirmé
- État de progression

**Actions:**
- Commander immédiatement si CRITIQUE
- Planifier si URGENT (7j)
- Optimiser si suffisant (14j+)

---

### 💼 Tab 3: FINANCE
Décisions financières critiques:

**Trésorerie - 4 Métriques**
1. **Trésorerie (Cash):** €2.05M (sain si > €500k)
2. **Net Debt:** €5-14M (à réduire si > €5M)
3. **Créances (AR):** À encaisser des clients
4. **Dettes (AP):** À payer aux fournisseurs

**Recommandation Paiement Dette**
- 🟢 **PAYER:** Si cash suffisant + net debt élevé
- 🟡 **GARDER CASH:** Si liquidité critique
- 🔵 **OPTIONNEL:** Si position confortable

**Rentabilité par Produit**
- Graphique bubble (Volume vs Marge vs Profit)
- Identifier les vaches à lait
- Détecter les produits problèmes

**Logique de Décision:**
```
SI Cash > €2M ET Net Debt > €5M:
  → Payer €500k-€1M de dette
  → Améliore credit rating
  → Réduit intérêts

SI Cash < €500k:
  → CONSERVER CASH
  → Pas de paiement dette
  → Priorité: trésorerie
```

---

### 🎯 Tab 4: RECOMMANDATIONS
Algorithmes d'optimisation:

**Portfolio Produits**
- Distribution optimale (pie chart)
- Focus sur top 6-8 produits (80% profit)
- Réduire tail de faibles marges

**Zones Prioritaires**
- Sélectionner un produit
- Voir le potentiel par zone
- Identifier où sous-représentés

**Prix Recommandés par Canal**
- Sélectionner produit
- Analyser prix optimal
- Par DC (10/12/14)
- Basé sur élasticité + competition

**Formule de Pricing:**
```
DC10 (Hypermarkets): Coût × 1.15 à 1.25 (sensibles prix)
DC12 (Grocery):      Coût × 1.30 à 1.50 (équilibré)
DC14 (Convenience):  Coût × 1.50 à 1.80 (peu sensibles)
```

---

### ⚡ Tab 5: ACTIONS RAPIDES
Outils opérationnels:

**📤 Exporter**
- Générer rapport Excel complet
- Toutes les données + analyses
- Partager avec team

**🔄 Actions de Gestion**
- Rafraîchir les données (force reload)
- Sauvegarder état

**📋 Checklist Quotidien**
- ✓ Vérifier ventes du jour
- ✓ Contrôler stocks critiques
- ✓ Prévisions livraisons
- ✓ Marges par produit
- ✓ Position financière
- ✓ Décision dette
- ✓ Ajuster prix
- ✓ Marketing

---

## 🎯 Cas d'Utilisation Typiques

### Matin - Check Rapide (5 min)
1. Ouvrir dashboard
2. Regarder KPIs principaux
3. Vérifier Tab 2 pour matériaux critiques
4. Vérifier Tab 3 pour cash position

### Décision Prix (15 min)
1. Tab 4: Sélectionner produit
2. Cliquer "Analyser les Prix"
3. Voir recommandations par canal
4. Implémenter dans SAP si applicable

### Gestion Stocks (20 min)
1. Tab 2: Voir matériaux critiques
2. Si 🔴 CRITIQUE: commander immédiatement
3. Si 🟠 URGENT: planifier commande
4. Vérifier ordres production

### Décision Financière (30 min)
1. Tab 3: Voir position cash
2. Lire recommandation paiement dette
3. Si action = PAYER: valider montant
4. Procéder en SAP

### Fin de Semaine - Analyse Complète (45 min)
1. Tab 1: Analyser ventes semaine
2. Tab 2: Planifier approvisionnement
3. Tab 3: Évaluer profitabilité
4. Tab 4: Revoir stratégie
5. Tab 5: Exporter rapport

---

## 📊 Indicateurs Clés à Surveiller

### Ventes
| Métrique | Bon | Alerte | Critique |
|----------|-----|--------|----------|
| Marge | > 65% | 55-65% | < 55% |
| Volume (qty) | Croissant | Stable | Décroissant |
| Mix produits | Concentré 6-8 | Dispersé | Tail trop long |

### Approvisionnement
| Métrique | Bon | Alerte | Critique |
|----------|-----|--------|----------|
| Jours stock | > 14j | 7-14j | < 3j |
| SKUs actifs | 8-12 | 12-15 | > 15 |
| Ruptures | 0 | 1-2 | > 2 |

### Finance
| Métrique | Bon | Alerte | Critique |
|----------|-----|--------|----------|
| Cash | > €1M | €500k-€1M | < €500k |
| Net Debt | < €3M | €3-5M | > €8M |
| Rating | A+ | A/BBB | B |

---

## 🔧 Configuration Avancée

### Personnaliser les Seuils
Dans `config.py`:
```python
LOW_STOCK_THRESHOLD_DAYS = 7  # Alerte
CRITICAL_STOCK_DAYS = 3       # Critique
MIN_CASH = 500_000            # Minimum recommandé
TARGET_NET_DEBT = 5_000_000   # Cible rating A+
```

### Ajouter des Métriques
Modifier les sections pertinentes du dashboard:
```python
# Dans tab3 (Finance), ajouter:
new_metric = analyzer.calculate_new_kpi()
st.metric("Nouvelle Métrique", new_metric)
```

---

## 📱 Responsive Design
Le dashboard s'adapte à:
- ✅ Desktop (full width)
- ✅ Tablet (2 colonnes)
- ✅ Mobile (1 colonne)

---

## 🆘 Troubleshooting

**Dashboard ne démarre pas**
→ Vérifier que Streamlit est installé: `pip install streamlit`

**Données vides**
→ Vérifier la connexion OData dans `.env`

**Lent**
→ Réduire `top=1000` dans les requêtes OData

**Boutons non fonctionnels**
→ Actualiser le navigateur (F5)

---

## 💡 Tips d'Utilisation

1. **Utiliser les filtres:** Sélectionner produits/zones spécifiques
2. **Exporter régulièrement:** Garder historique des rapports
3. **Raffraîchir souvent:** Les données changent chaque jour
4. **Mobile check:** Regarder le dashboard sur téléphone pour format adapté
5. **Notes:** Prendre notes des décisions prises

---

## 🚀 Prochaines Améliorations

- [ ] Alertes email automatiques
- [ ] Prévisions ML (Prophet)
- [ ] Comparaison historique
- [ ] Budgétisation marketing
- [ ] Simulation scénarios
- [ ] Intégration SAP directe (WS)
