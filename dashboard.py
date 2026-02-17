
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analyzer import ERPSimAnalyzer
from sales_engine import SalesEngine
from finance_engine import FinanceEngine
from procurement_engine import ProcurementEngine
from config import settings
import time

# --- Configuration de la page ---
st.set_page_config(
    page_title=f"ERPsim Strategy Pro - {settings.COMPANY_CODE}",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Personnalisé ---
st.markdown("""
<style>
    .main { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 4px;
        padding: 8px 16px; 
    }
    .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialisation ---
@st.cache_resource
def get_analyzer(): return ERPSimAnalyzer()

@st.cache_resource
def get_engines(_analyzer):
    return {
        'sales': SalesEngine(_analyzer),
        'finance': FinanceEngine(_analyzer),
        'procurement': ProcurementEngine(_analyzer)
    }

try:
    analyzer = get_analyzer()
    engines = get_engines(analyzer)
except Exception as e:
    st.error(f"Erreur connexion: {e}")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.title("🎛️ Contrôle")
    if st.button("🔄 Rafraîchir Données", type="primary"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.divider()
    
    # --- Filtre Produits ---
    st.subheader("🎯 Filtre Produits")
    
    # --- Filtre Produits ---
    st.subheader("🎯 Filtre Produits")
    
    # 1. Récupérer tous les produits
    all_products = engines['sales'].get_active_products() 
    
    active_products = []
    
    if all_products:
        # Option: Boutons pour tout cocher/décocher (Session State pour gérer l'état)
        # Pour faire simple et robuste : Checkboxes individuelles
        
        st.write("Cochez les produits à analyser :")
        
        for p in all_products:
            # On cherche une description si dispo dans le cache analyzer (optionnel mais sympa)
            # Sinon on affiche juste le code
            label = p
            
            # Checkbox par défaut = True
            if st.checkbox(label, value=True, key=f"filter_{p}"):
                active_products.append(p)
                
    else:
        st.info("Aucun produit actif détecté.")

    st.divider()

    st.info("💡 **Conseil du jour:** Rembourser la dette est souvent l'action la plus rentable pour la valorisation.")

# --- Header KPIs ---
st.title(f"🚀 ERPsim Strategy - {settings.COMPANY_CODE}")

with st.spinner('Chargement...'):
    val_df = analyzer.get_company_valuation()
    if not val_df.empty:
        latest = val_df.iloc[-1]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Valorisation", f"€{float(latest.get('COMPANY_VALUATION', 0)):,.0f}")
        col2.metric("Cash (Banque)", f"€{float(latest.get('BANK_CASH_ACCOUNT', 0)):,.0f}")
        col3.metric("Profit Net", f"€{float(latest.get('PROFIT', 0)):,.0f}")
        col4.metric("Dette Bancaire", f"€{float(latest.get('BANK_LOAN', 0)):,.0f}")
        col5.metric("Rating", latest.get('CREDIT_RATING', 'N/A'))
    else:
        st.warning("Pas de données KPI")

st.markdown("---")

# --- Tabs ---
tab_sales, tab_inventory, tab_market, tab_marketing, tab_invest, tab_actions = st.tabs([
    "📈 VENTES (Produits)", 
    "📦 STOCKS (Finis)", 
    "🏆 MARCHÉ (Zmarket)",
    "📣 MARKETING (Ciblé)", 
    "💰 INVESTISSEMENT (Stratégie)",
    "⚡ ACTIONS"
])

# --- 1. VENTES ---
with tab_sales:
    st.subheader("Analyse des Ventes & Prix (Produits Finis uniquement)")
    
    # Récupérer les données
    sales_summary = analyzer.get_sales_summary()
    recos = engines['sales'].recommend_price_adjustments()
    
    if not sales_summary.empty:
        # Filtrage: Ne garder que ce qui a un prix définit (Produits finis)
        # On utilise la liste 'active_products' définie dans la sidebar
        
        # Filtrer sales summary
        df_display = sales_summary[sales_summary['MATERIAL_NUMBER'].isin(active_products)].copy()
        
        if not df_display.empty:
            # Ajouter colonne Recommandation si dispo
            if not recos.empty:
                # Merge logic simplification
                reco_map = recos.set_index('Produit')['Action'].to_dict()
                df_display['Conseil Prix'] = df_display['MATERIAL_NUMBER'].map(reco_map).fillna("-")
            else:
                df_display['Conseil Prix'] = "-"

            # Affichage Table Principale
            st.dataframe(
                df_display[['MATERIAL_DESCRIPTION', 'NET_VALUE', 'PROFIT', 'MARGIN_PCT', 'Conseil Prix']]
                .style.format({'NET_VALUE': '€{:,.0f}', 'PROFIT': '€{:,.0f}', 'MARGIN_PCT': '{:.1f}%'})
                .background_gradient(subset=['MARGIN_PCT'], cmap='Greens'),
                use_container_width=True
            )
            
    # --- 2. Analyse Détaillée (Région & Magasins) ---
    st.subheader("📊 Analyse Détaillée : Marges & Prix")
    
    tab_geo, tab_store = st.tabs(["🌍 Par Région", "🏪 Par Type de Magasin (DC)"])
    
    with tab_geo:
        sales_geo = analyzer.get_sales_by_product_and_area()
        if not sales_geo.empty:
            # Filtre Produit
            if active_products:
                sales_geo = sales_geo[sales_geo['MATERIAL_NUMBER'].isin(active_products)]
            
            # Formatage pour affichage
            display_geo = sales_geo[['MATERIAL_DESCRIPTION', 'AREA', 'NET_VALUE', 'PROFIT', 'MARGIN_PCT', 'AVG_PRICE', 'QUANTITY']].copy()
            
            st.dataframe(
                display_geo.style
                .format({'NET_VALUE': '€{:,.0f}', 'PROFIT': '€{:,.0f}', 'MARGIN_PCT': '{:.1f}%', 'AVG_PRICE': '€{:.2f}', 'QUANTITY': '{:,.0f}'})
                .background_gradient(subset=['MARGIN_PCT'], cmap='RdYlGn', vmin=0, vmax=60)
                .background_gradient(subset=['NET_VALUE'], cmap='Blues'),
                use_container_width=True
            )
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                 # Graphique Marge par Région
                 fig_margin_geo = px.bar(sales_geo, x='AREA', y='MARGIN_PCT', color='MATERIAL_NUMBER', barmode='group', 
                                         title="Marge % par Région et Produit")
                 st.plotly_chart(fig_margin_geo, use_container_width=True)
        else:
            st.info("Pas de données régionales.")

    with tab_store:
        sales_dc = analyzer.get_sales_by_product_and_dc()
        if not sales_dc.empty:
            # Filtre Produit
            if active_products:
                sales_dc = sales_dc[sales_dc['MATERIAL_NUMBER'].isin(active_products)]
                
            display_dc = sales_dc[['MATERIAL_DESCRIPTION', 'DISTRIBUTION_CHANNEL', 'NET_VALUE', 'PROFIT', 'MARGIN_PCT', 'AVG_PRICE', 'QUANTITY']].copy()
            
            st.dataframe(
                display_dc.style
                .format({'NET_VALUE': '€{:,.0f}', 'PROFIT': '€{:,.0f}', 'MARGIN_PCT': '{:.1f}%', 'AVG_PRICE': '€{:.2f}', 'QUANTITY': '{:,.0f}'})
                .background_gradient(subset=['MARGIN_PCT'], cmap='RdYlGn', vmin=0, vmax=60)
                .background_gradient(subset=['AVG_PRICE'], cmap='Purples'),
                use_container_width=True
            )
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                 # Prix Moyen par DC
                 fig_price_dc = px.bar(sales_dc, x='DISTRIBUTION_CHANNEL', y='AVG_PRICE', color='MATERIAL_NUMBER', barmode='group',
                                       title="Prix de Vente Moyen par Canal")
                 st.plotly_chart(fig_price_dc, use_container_width=True)
        else:
            st.info("Pas de données par canal.")

    st.divider()

    # --- 3. Zones & Canaux (Globaux) ---
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🌍 Répartition Géographique (Globale)")
        sales_geo = analyzer.get_sales_by_area()
        if not sales_geo.empty:
            fig = px.pie(sales_geo, values='NET_VALUE', names='AREA', title="CA par Région")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas de données.")

    with col4:
        st.subheader("📦 Répartition par Canal (Globale)")
        sales_dc = analyzer.get_sales_by_dc()
        if not sales_dc.empty:
             fig = px.pie(sales_dc, values='NET_VALUE', names='DISTRIBUTION_CHANNEL', title="CA par Canal")
             st.plotly_chart(fig, use_container_width=True)
        else:
             st.info("Pas de données.")

# --- 2. STOCKS ---
with tab_inventory:
    st.subheader("📦 Stock Produits Finis")
    
    inventory = analyzer.get_current_inventory()
    
    if not inventory.empty:
        # FILTRE: Uniquement produits finis (active_products)
        if active_products:
             df_finished = inventory[inventory['MATERIAL_NUMBER'].isin(active_products)].copy()
        else:
             df_finished = inventory.copy()
        
        if not df_finished.empty:
            if 'STOCK' in df_finished.columns:
                df_finished['STOCK'] = pd.to_numeric(df_finished['STOCK'], errors='coerce')
                
            total_stock = df_finished['STOCK'].sum()
            
            # Alerte Stock Global
            col_kpi1, col_kpi2 = st.columns(2)
            col_kpi1.metric("Total Unités en Stock", f"{total_stock:,.0f}")
            
            if total_stock > 250_000:
                col_kpi2.error(f"⚠️ SURSTOCK CRITIQUE: {total_stock:,.0f} > 250k ! Arrêtez la production.")
            elif total_stock < 50_000:
                 col_kpi2.warning(f"⚠️ RISQUE RUPTURE: {total_stock:,.0f} unités. Produisez !")
            else:
                col_kpi2.success("✅ Niveau de stock sain.")
                
            # Table détaillée
            st.dataframe(
                df_finished[['MATERIAL_DESCRIPTION', 'STOCK', 'RESTRICTED']]
                .style.bar(subset=['STOCK'], color='#5fba7d'),
                use_container_width=True
            )
        else:
            st.info("Aucun stock de produits finis.")
    else:
        st.info("Inventaire vide.")

# --- 3. MARCHÉ (Zmarket) ---
with tab_market:
    st.subheader("🏆 Analyse du Marché (Zmarket vs Nous)")
    
    market_analysis = analyzer.get_market_analysis()
    
    if not market_analysis.empty:
        # Toggle pour voir tout le marché ou juste nos produits
        show_all = st.toggle("Voir tous les produits du marché (même ceux qu'on ne vend pas)", value=False)
        
        if not show_all and active_products:
             market_analysis = market_analysis[market_analysis['MATERIAL_NUMBER'].isin(active_products)]
             
        # KPIs globaux
        total_market = market_analysis['MARKET_VALUE'].sum()
        my_total = market_analysis['MY_VALUE'].sum()
        global_share = (my_total / total_market * 100) if total_market > 0 else 0
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Taille Marché Total", f"€{total_market:,.0f}")
        col_m2.metric("Nos Ventes Totales", f"€{my_total:,.0f}")
        col_m3.metric("Part de Marché Globale", f"{global_share:.1f}%")
        
        # Graphique Scatter: Part de marché vs Taille du marché
        fig_market = px.scatter(
            market_analysis, 
            x='MARKET_VALUE', 
            y='MARKET_SHARE',
            size='MARKET_VALUE',
            color='STATUS',
            hover_name='MATERIAL_DESCRIPTION',
            text='MATERIAL_NUMBER',
            title="Matrice Opportunités : Taille Marché vs Part de Marché",
            color_discrete_map={
                "⭐ Star": "green", 
                "🎯 Opportunité": "blue", 
                "🛡️ Niche": "orange", 
                "💤 Faible": "grey"
            }
        )
        # Ligne médiane pour visualiser les quadrants
        fig_market.add_hline(y=market_analysis['MARKET_SHARE'].median(), line_dash="dash", line_color="red", annotation_text="Part Median")
        fig_market.add_vline(x=market_analysis['MARKET_VALUE'].median(), line_dash="dash", line_color="red", annotation_text="Taille Median")
        
        st.plotly_chart(fig_market, use_container_width=True)
        
        st.markdown("### 📋 Détail par Produit")
        st.dataframe(
            market_analysis[['MATERIAL_DESCRIPTION', 'MARKET_VALUE', 'MY_VALUE', 'MARKET_SHARE', 'STATUS']]
            .style
            .format({'MARKET_VALUE': '€{:,.0f}', 'MY_VALUE': '€{:,.0f}', 'MARKET_SHARE': '{:.1f}%'})
            .background_gradient(subset=['MARKET_SHARE'], cmap='Greens')
            .bar(subset=['MARKET_VALUE'], color='#e0e0e0'),
            use_container_width=True
        )
        
    else:
        st.info("Données Zmarket non disponibles pour le moment.")

# --- 4. MARKETING ---
with tab_marketing:
    st.subheader("🎯 Stratégie Marketing Ciblée")
    
    reco_marketing = engines['sales'].recommend_marketing_strategy()
    
    # Filtrer avec le sélecteur sidebar
    if not reco_marketing.empty and active_products:
        # La colonne Produit est "Code - Description", on filtre sur le code
        reco_marketing = reco_marketing[reco_marketing['Produit'].apply(lambda x: any(p in x for p in active_products))]
    
    if not reco_marketing.empty:
        st.info("💡 **Logique:** Investir sur les 500g (Haute sensibilité) et couper les ruptures.")
        
        # Style conditionnel
        def color_coding(val):
            color = 'black'
            if 'STOP' in str(val): color = 'red'
            elif '+++' in str(val): color = 'green'
            elif '++' in str(val): color = 'blue'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            reco_marketing.style.applymap(color_coding, subset=['NORD', 'SUD', 'OUEST']),
            use_container_width=True
        )
    else:
        st.warning("Impossible de générer la stratégie marketing (manque de données).")

# --- 5. INVESTISSEMENT ---
with tab_invest:
    st.header("💰 Stratégie d'Investissement & Cash Flow")
    
    # Calculs Financiers
    fin_analysis = engines['finance'].analyze_cash_position()
    
    if fin_analysis:
        current_profit = fin_analysis.get('profit', 0)
        current_net_debt = fin_analysis.get('net_debt', 0)
        
        # --- SECTION DETTE ---
        st.subheader("1. Gestion de la Dette (Impact Valorisation)")
        
        impact_data = engines['finance'].calculate_valuation_impact(current_profit, current_net_debt)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.metric("Dette Nette Actuelle", f"€{current_net_debt:,.0f}", delta_color="inverse")
            st.metric("Cote Actuelle (Estimée)", f"{fin_analysis.get('credit_rating', 'N/A')}")
        
        with col_d2:
            st.write(f"**Gain potentiel de valorisation :** €{impact_data['impact_value']:,.0f}")
            st.progress(min(1.0, max(0.0, impact_data['current_valuation'] / impact_data['potential_valuation'] if impact_data['potential_valuation'] > 0 else 0)))
            
            if impact_data['is_optimized']:
                st.success("✅ Dette Optimisée ! Vous avez le meilleur taux.")
            else:
                if current_net_debt > 1_000_000:
                    pay_amount = current_net_debt - 1_000_000
                    st.error(f"👉 **ACTION:** Remboursez €{pay_amount:,.0f} pour viser AAA+.")
        
        st.divider()
        
        # --- SECTION STOCK ---
        st.subheader("2. Coût du Stock (Cash Trap)")
        stock_costs = engines['finance'].calculate_stock_costs()
        
        if stock_costs:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("Argent Bloqué (Cash Trap)", f"€{stock_costs['cash_trap']:,.0f}")
                st.metric("Unités Totales", f"{stock_costs['total_units']:,.0f}")
                
            with col_s2:
                if stock_costs['is_critical']:
                    st.error(f"🚨 **ALERTE:** Vous perdez de l'argent ! Stock > 250k.")
                    st.write(f"Coût stockage estimé: **€{stock_costs['storage_fees_daily']} / jour**")
                    st.write("👉 Arrêtez les achats de matières premières immédiatement.")
                else:
                    st.success("✅ Niveau de stock acceptable (< 250k).")
        
        st.divider()
        
        # --- SECTION SETUP ---
        st.subheader("3. Investissement Production (Setup Time)")
        
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            daily_changeovers = st.slider("Changements de produits par jour (Est.)", 1, 10, 3)
            roi_data = engines['finance'].calculate_setup_roi(daily_changeovers)
            
        with col_i2:
            st.metric("Gain quotidien estimé", f"€{roi_data['daily_gain']:,.0f}")
            st.metric("ROI (Jours)", f"{roi_data['days_to_roi']} jours")
            
            if roi_data['days_to_roi'] < 15:
                st.success(f"🚀 **FONCEZ !** L'investissement de 50k€ est rentabilisé en {roi_data['days_to_roi']} jours.")
            else:
                st.warning("Investissement risqué si la simulation est presque finie.")

# --- 6. ACTIONS ---
with tab_actions:
    st.subheader("⚡ Actions Rapides")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Télécharger Rapport Excel Global"):
            with st.spinner("Génération..."):
                report = analyzer.generate_performance_report()
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                     for name, df in report.items():
                         if not df.empty: df.to_excel(writer, sheet_name=name[:30], index=False)
                st.download_button("Télécharger .xlsx", buffer, "erpsim_report.xlsx")
    
    with col2:
        st.write("Autres actions à venir...")
