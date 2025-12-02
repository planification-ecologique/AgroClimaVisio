# Déploiement sur Railway

Ce guide explique comment déployer l'API et le frontend AgroClimaVisio sur Railway.

## Architecture Railway

Railway peut déployer plusieurs services dans un même projet :
- **Service Backend** : API FastAPI (Python)
- **Service Frontend** : Application React/Vite (Node.js)

## Prérequis

1. Un compte Railway (gratuit jusqu'à $5/mois de crédits)
2. Le projet Git configuré
3. La base de données DuckDB doit être téléversée séparément (voir ci-dessous)

## Configuration des fichiers

Les fichiers de configuration sont à la **racine** du projet :

- `Procfile` : Commande de démarrage pour le backend (Railway détecte automatiquement)
- `railway.json` : Configuration Railway pour le backend
- `nixpacks.toml` : Configuration Nixpacks pour Poetry

**Important** : Les fichiers dans `backend/` ne sont **pas** nécessaires pour Railway, seulement ceux à la racine.

## Étapes de déploiement

### 1. Créer un projet Railway

1. Allez sur [railway.app](https://railway.app)
2. Connectez-vous avec GitHub
3. Cliquez sur "New Project"
4. Sélectionnez "Deploy from GitHub repo"
5. Choisissez votre repository AgroClimaVisio

### 2. Déployer le Backend

Railway devrait automatiquement détecter le `Procfile` et créer un service backend.

1. Si Railway ne détecte pas automatiquement :
   - Cliquez sur "+ New" → "GitHub Repo"
   - Sélectionnez votre repo
   - Railway devrait détecter le `Procfile` et créer un service Python

2. **Configurer le Root Directory** :
   - Dans les paramètres du service backend
   - Laissez "Root Directory" vide (Railway utilisera le `Procfile` qui change vers `backend/`)

3. **Variables d'environnement** :
   - `CORS_ORIGINS` : URLs du frontend (ex: `https://votre-frontend.up.railway.app,http://localhost:5173`)
   - Ajoutez d'autres variables si nécessaire

### 3. Déployer le Frontend

1. Dans le même projet Railway, cliquez sur "+ New" → "GitHub Repo"
2. Sélectionnez le même repository
3. Railway devrait détecter `frontend/package.json` et créer un service Node.js

4. **Configurer le Root Directory** :
   - Dans les paramètres du service frontend → "Settings" → "Root Directory"
   - Définissez "Root Directory" à `frontend`
   - Railway cherchera le `Procfile` dans `frontend/` ou utilisera la détection automatique

5. **Variables d'environnement** :
   - `VITE_API_URL` : URL du service backend Railway (ex: `https://votre-backend.up.railway.app`)
   - `NODE_ENV` : `production`
   - **Important** : Utilisez l'URL publique du backend Railway, pas `localhost`

6. **Build Command** (automatique ou manuel) :
   - Railway détecte automatiquement : `npm install && npm run build`
   - Ou définissez manuellement : `npm install && npm run build`

7. **Start Command** :
   - Si `frontend/Procfile` existe : Railway l'utilisera automatiquement
   - Sinon, définissez manuellement : `npm run preview -- --host 0.0.0.0 --port $PORT`
   - Ou utilisez un serveur statique : `npx serve -s dist -l $PORT`

### 4. Téléverser la base de données DuckDB

La base de données `climate_data.duckdb` doit être disponible pour le backend.

#### Option A : Volume persistant Railway (recommandé)

1. Dans le service backend, ajoutez un "Volume"
2. Montez-le sur `/app/backend/climate_data.duckdb`
3. Téléversez votre fichier `climate_data.duckdb` dans le volume

#### Option B : Stockage cloud (S3, etc.)

1. Téléversez `climate_data.duckdb` sur un service de stockage cloud
2. Modifiez `duckdb_loader.py` pour télécharger depuis le cloud au démarrage
3. Configurez les variables d'environnement pour les credentials

### 5. Vérifier les déploiements

**Backend** :
```bash
curl https://votre-backend.up.railway.app/health
```

**Frontend** :
- Ouvrez l'URL fournie par Railway
- Vérifiez que les requêtes API fonctionnent

## Structure des fichiers

```
/
├── Procfile              # Commande de démarrage backend (à la racine)
├── railway.json          # Configuration Railway backend (à la racine)
├── nixpacks.toml         # Configuration Nixpacks pour Poetry (à la racine)
├── backend/
│   ├── pyproject.toml    # Dépendances Poetry
│   ├── main.py           # Application FastAPI
│   └── climate_data.duckdb   # Base de données (à téléverser)
└── frontend/
    ├── Procfile          # Commande de démarrage frontend (optionnel)
    ├── package.json      # Dépendances Node.js
    ├── vite.config.ts    # Configuration Vite
    └── src/              # Code source React
```

**Note** : Les fichiers de configuration Railway sont à la racine pour le backend, et dans `frontend/` pour le frontend. Pas besoin de doublons !

## Configuration des services Railway

### Service Backend

- **Root Directory** : (vide ou `/`)
- **Build Command** : (automatique via nixpacks.toml)
- **Start Command** : (automatique via Procfile)
- **Port** : Automatique (`$PORT`)

### Service Frontend

- **Root Directory** : `frontend`
- **Build Command** : `npm install && npm run build`
- **Start Command** : `npx serve -s dist -l $PORT` ou `npm run preview -- --host 0.0.0.0 --port $PORT`
- **Port** : Automatique (`$PORT`)

## Variables d'environnement

### Backend

- `CORS_ORIGINS` : URLs autorisées (séparées par des virgules)
  - Exemple : `https://votre-frontend.up.railway.app,http://localhost:5173`

### Frontend

- `VITE_API_URL` : URL de l'API backend
  - Exemple : `https://votre-backend.up.railway.app`
- `NODE_ENV` : `production`

## Notes importantes

- **Deux services séparés** : Backend et Frontend sont déployés comme deux services distincts dans Railway
- **Communication** : Le frontend appelle le backend via l'URL publique Railway
- **CORS** : Configurez `CORS_ORIGINS` dans le backend pour autoriser le frontend
- **Base de données** : Assurez-vous que `climate_data.duckdb` est accessible au backend
- **Ports** : Railway gère automatiquement les ports via `$PORT`

## Dépannage

### "No start command was found"

- Vérifiez que le `Procfile` est bien à la racine du projet
- Vérifiez que Railway utilise le bon repository

### Erreurs CORS

- Vérifiez que `CORS_ORIGINS` contient l'URL exacte du frontend Railway
- Les URLs doivent être exactes (avec/sans trailing slash)

### Frontend ne trouve pas l'API

- Vérifiez que `VITE_API_URL` est correctement configuré
- Vérifiez que l'URL du backend est accessible publiquement
- Vérifiez les logs du frontend dans Railway

### Base de données non trouvée

- Vérifiez que le fichier `climate_data.duckdb` est bien téléversé
- Vérifiez le chemin dans `duckdb_loader.py`
- Considérez utiliser un volume persistant Railway

## Coûts

Railway offre :
- **Gratuit** : $5 de crédits par mois
- **Hobby** : $5/mois pour plus de ressources
- **Pro** : $20/mois pour des ressources dédiées

Pour une API + Frontend avec une base de données de 150MB, le plan gratuit devrait suffire pour les tests.

