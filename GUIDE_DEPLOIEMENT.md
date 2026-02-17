# 🚀 Guide de Déploiement : ERPsim Dashboard

Puisque ton code est maintenant sur GitHub, tu peux le déployer gratuitement et facilement sur **Streamlit Community Cloud**.

## Étape 1 : Connexion
1.  Va sur [share.streamlit.io](https://share.streamlit.io/).
2.  Connecte-toi avec ton compte **GitHub**.

## Étape 2 : Créer l'application
1.  Clique sur le bouton bleu **"New app"** (ou "Deploy an app").
2.  Remplis le formulaire :
    *   **Repository :** `Benjamin987Hustle/Progiciel`
    *   **Branch :** `main`
    *   **Main file path :** `dashboard.py`

## Étape 3 : Configurer les Secrets (TRES IMPORTANT ⚠️)
Comme le fichier `.env` (qui contient tes mots de passe) n'est **pas** sur GitHub par sécurité, tu dois le donner à Streamlit manuellement.

1.  Clique sur **"Advanced settings..."** (en bas du formulaire).
2.  Dans la fenêtre qui s'ouvre, va dans l'onglet **"Secrets"**.
3.  Copie-colle le bloc ci-dessous dans la zone de texte :

```toml
ODATA_BASE_URL = "https://sapvm2.hec.ca:8001/odata/300"
ODATA_USERNAME = "H_5"
ODATA_PASSWORD = "Canada1"
COMPANY_CODE = "H2"
PLANT = "1000"
CACHE_ENABLED = true
DEBUG = false
REFRESH_RATE = 30
```

*(Note : J'ai adapté le format pour Streamlit, c'est du TOML, donc `true`/`false` en minuscules).*

4.  Clique sur **"Save"**.

## Étape 4 : Lancer
1.  Clique sur le bouton **"Deploy!"**.
2.  Attends quelques minutes que l'installation se fasse (il va installer automatiquement les bibliothèques listées dans `requirements.txt`).

---
🎉 **Bravo !** Ton dashboard sera accessible via une URL publique (du type `https://progiciel-dashboard.streamlit.app`) que tu pourras partager à ton équipe.
