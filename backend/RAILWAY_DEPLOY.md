# Déploiement sur Railway

Ce guide explique comment déployer l'API AgroClimaVisio sur Railway.

## Prérequis

1. Un compte Railway (gratuit jusqu'à $5/mois de crédits)
2. Le projet Git configuré
3. La base de données DuckDB doit être téléversée séparément (voir ci-dessous)

## Étapes de déploiement

### 1. Préparer le projet

Les fichiers de configuration sont déjà en place :
- `Procfile` : Définit comment démarrer l'application
- `railway.json` : Configuration Railway
- `pyproject.toml` : Dépendances Python avec Poetry

### 2. Créer un projet Railway

1. Allez sur [railway.app](https://railway.app)
2. Connectez-vous avec GitHub
3. Cliquez sur "New Project"
4. Sélectionnez "Deploy from GitHub repo"
5. Choisissez votre repository AgroClimaVisio
6. Railway détectera automatiquement le dossier `backend/`

### 3. Configurer les variables d'environnement

Dans les paramètres du projet Railway, ajoutez :

- **CORS_ORIGINS** : Les origines autorisées pour CORS (séparées par des virgules)
  - Exemple : `https://votre-frontend.vercel.app,http://localhost:5173`
  - Par défaut : `http://localhost:5173`

### 4. Téléverser la base de données DuckDB

La base de données `climate_data.duckdb` doit être disponible sur Railway. Options :

#### Option A : Volume persistant Railway (recommandé)

1. Dans Railway, ajoutez un "Volume" au projet
2. Montez-le sur `/app/climate_data.duckdb`
3. Téléversez votre fichier `climate_data.duckdb` dans le volume

#### Option B : Stockage cloud (S3, etc.)

1. Téléversez `climate_data.duckdb` sur un service de stockage cloud
2. Modifiez `duckdb_loader.py` pour télécharger depuis le cloud au démarrage
3. Configurez les variables d'environnement pour les credentials

#### Option C : Inclure dans le repo (non recommandé pour production)

⚠️ **Attention** : La base de données fait ~150MB, ce qui peut ralentir les déploiements.

### 5. Déployer

Railway déploiera automatiquement à chaque push sur la branche principale.

Pour déployer manuellement :
1. Railway détectera automatiquement Poetry
2. Installera les dépendances
3. Exécutera la commande du `Procfile`

### 6. Vérifier le déploiement

Une fois déployé, Railway vous donnera une URL comme :
`https://votre-projet.up.railway.app`

Testez l'API :
```bash
curl https://votre-projet.up.railway.app/health
```

### 7. Mettre à jour le frontend

Mettez à jour `VITE_API_URL` dans votre frontend pour pointer vers l'URL Railway.

## Structure des fichiers

```
backend/
├── Procfile              # Commande de démarrage Railway
├── railway.json          # Configuration Railway
├── .railwayignore        # Fichiers à ignorer
├── pyproject.toml        # Dépendances Poetry
├── main.py               # Application FastAPI
└── climate_data.duckdb   # Base de données (à téléverser)
```

## Notes importantes

- **Port** : Railway définit automatiquement `$PORT`, le code l'utilise déjà
- **CORS** : Configurez `CORS_ORIGINS` pour autoriser votre frontend
- **Base de données** : Assurez-vous que `climate_data.duckdb` est accessible
- **Logs** : Consultez les logs dans le dashboard Railway en cas de problème

## Dépannage

### L'application ne démarre pas

1. Vérifiez les logs dans Railway
2. Assurez-vous que Poetry est installé (Railway le détecte automatiquement)
3. Vérifiez que `climate_data.duckdb` existe et est accessible

### Erreurs CORS

1. Vérifiez que `CORS_ORIGINS` contient l'URL de votre frontend
2. Les URLs doivent être exactes (avec/sans trailing slash)

### Base de données non trouvée

1. Vérifiez que le fichier `climate_data.duckdb` est bien téléversé
2. Vérifiez le chemin dans `duckdb_loader.py`
3. Considérez utiliser un volume persistant Railway

## Coûts

Railway offre :
- **Gratuit** : $5 de crédits par mois
- **Hobby** : $5/mois pour plus de ressources
- **Pro** : $20/mois pour des ressources dédiées

Pour une API avec une base de données de 150MB, le plan gratuit devrait suffire pour les tests.

