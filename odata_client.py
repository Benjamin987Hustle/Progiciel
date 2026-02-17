"""
Client OData pour connexion à ERPsim
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional
import pandas as pd
from config import settings
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ODataClient:
    """Client pour se connecter à l'API OData ERPsim"""

    def __init__(self):
        self.base_url = settings.ODATA_BASE_URL.rstrip('/')
        self.auth = HTTPBasicAuth(settings.ODATA_USERNAME, settings.ODATA_PASSWORD)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.verify = False
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def fetch_view(self, view_name: str, filters: Optional[Dict] = None,
                   top: Optional[int] = None) -> pd.DataFrame:
        """
        Récupère les données d'une vue OData

        Args:
            view_name: Nom de la vue (ex: "Sales", "Current_Inventory")
            filters: Filtres OData (ex: {"COMPANY_CODE": "ZZ01"})
            top: Nombre max de résultats

        Returns:
            DataFrame avec les données
        """
        url = f"{self.base_url}/{view_name}"

        params = {}

        # Filtres
        if filters:
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key} eq '{value}'")
                else:
                    filter_parts.append(f"{key} eq {value}")
            if filter_parts:
                params['$filter'] = ' and '.join(filter_parts)

        # Limite de résultats
        if top:
            params['$top'] = top

        try:
            logger.info(f"Fetching {view_name}...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extraire les résultats
            if 'd' in data and 'results' in data['d']:
                results = data['d']['results']
            elif 'd' in data and 'EntitySets' in data['d']:
                results = data['d']['EntitySets']
            elif 'value' in data:
                results = data['value']
            else:
                results = []

            df = pd.DataFrame(results)
            logger.info(f"✓ Récupéré {len(df)} lignes depuis {view_name}")

            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Erreur lors de la récupération de {view_name}: {e}")
            return pd.DataFrame()

    def test_connection(self) -> bool:
        """Teste la connexion à l'API"""
        try:
            logger.info("Test de connexion OData...")

            # Essayer de récupérer les règles du jeu (petite requête)
            df = self.fetch_view("Current_Game_Rules", top=5)

            if not df.empty:
                logger.info("✓ Connexion OData réussie!")
                return True
            else:
                logger.warning("⚠ Connexion réussie mais aucune donnée retournée")
                return True  # Connexion ok, juste pas de données

        except Exception as e:
            logger.error(f"✗ Échec de connexion: {e}")
            return False

    def get_available_entity_sets(self) -> List[str]:
        """Récupère la liste des EntitySets disponibles"""
        try:
            url = self.base_url
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'd' in data and 'EntitySets' in data['d']:
                return data['d']['EntitySets']
            else:
                return []

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des EntitySets: {e}")
            return []
