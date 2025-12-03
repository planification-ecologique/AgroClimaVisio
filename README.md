# AgroClimaVisio

AgroClimaVisio est une interface de visualisation agro‑climatique permettant aux agriculteurs, coopératives, conseillers et chercheurs de comprendre l'évolution du climat à l'échelle locale, pour mieux anticiper les risques (sécheresse, excès d'eau, orages violents) et optimiser les décisions agronomiques.

## 🚀 Technologies

- **Frontend**: Vite + React + TypeScript + Recharts + MapLibre GL
- **Backend**: FastAPI (Python)
- **Base de données**: DuckDB (OLAP in-process)
- **Données climatiques**: NetCDF (Météo-France DRIAS)
- **Gestion de dépendances**: Poetry (backend), Yarn (frontend)
- **Cartes**: MapLibre GL

## 📋 Prérequis

- Node.js 20+ et Yarn 1.22+
- Python 3.9+
- Poetry

## 🛠️ Installation

### Installation de Poetry (si nécessaire)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Frontend

```bash
cd frontend
yarn install
```

### Backend

```bash
cd backend
poetry install
```

## 🏃 Démarrage

### Backend (Terminal 1)

```bash
cd backend
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Ou avec shell Poetry :
```bash
cd backend
poetry shell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur http://localhost:8000
Documentation API: http://localhost:8000/docs

### Frontend (Terminal 2)

```bash
cd frontend
yarn dev
```

L'application sera accessible sur http://localhost:5173

## 📁 Structure du projet

```
AgroClimaVisio/
├── frontend/              # Application React + Vite
│   ├── src/
│   │   ├── components/    # Composants React (charts, maps, etc.)
│   │   ├── pages/         # Pages de l'application
│   │   ├── types.ts       # Types TypeScript
│   │   └── App.tsx        # Composant principal
│   ├── package.json
│   └── yarn.lock
├── backend/               # API FastAPI
│   ├── main.py            # Point d'entrée de l'API
│   ├── duckdb_loader.py   # Chargeur DuckDB pour données climatiques
│   ├── import_to_duckdb.py # Script d'import NetCDF → DuckDB
│   ├── points_config.py   # Configuration des points géographiques
│   ├── data/              # Données NetCDF et base DuckDB
│   │   └── climate_data.duckdb
│   ├── pyproject.toml     # Configuration Poetry
│   └── models.py          # Modèles de données
└── README.md
```

## 🎯 Fonctionnalités

### Visualisation de données climatiques
- **Graphiques mensuels** : Précipitations et températures pour plusieurs villes et membres d'ensemble
- **Faisabilité des couverts végétaux** : Analyse de la faisabilité selon les précipitations (fenêtres glissantes)
- **Viabilité du maïs** : Analyse multi-critères (semis, croissance, récolte)
- **Données historiques et projetées** : Comparaison entre périodes historiques (1990-2014) et projections (2015-2100)

### Indicateurs agro-climatiques
- **Couverts végétaux** : Analyse des fenêtres de précipitations optimales (21 et 42 jours)
- **Viabilité maïs** : Critères de semis (cumul pluie), croissance (fenêtres glissantes), récolte (sécheresse)

### Données
- **Base de données DuckDB** : Stockage optimisé pour requêtes analytiques rapides
- **Import NetCDF** : Import automatique des fichiers climatiques Météo-France
- **Points géographiques** : 12 villes représentatives (Beauce, Bretagne, et autres régions)

### API
- **Endpoints REST** : API complète pour accéder aux données climatiques
- **Documentation interactive** : Swagger UI disponible sur `/docs`
- **SQL Query Panel** : Interface de développement pour requêtes SQL directes (mode dev)

## 🔧 Configuration

### Variables d'environnement

**Frontend** (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

**Backend** (`backend/.env` - optionnel):
```env
CORS_ORIGINS=http://localhost:5173,https://agroclimavisio.surge.sh
DUCKDB_PATH=/path/to/db  # Chemin vers la base DuckDB (optionnel)
```

## 📊 Import des données climatiques

### Préparation des données

1. **Télécharger les fichiers NetCDF** depuis data.gouv.fr (Météo-France DRIAS)
   ```bash
   cd backend
   poetry run python download_emul_ssp370.py --experiment historical --download
   poetry run python download_emul_ssp370.py --experiment ssp370 --download
   ```

2. **Placer les fichiers** dans `backend/data/`

3. **Importer dans DuckDB**
   ```bash
   cd backend
   poetry run python import_to_duckdb.py
   ```

Le script importe automatiquement les données pour tous les points géographiques configurés dans `points_config.py`.

### Points géographiques disponibles

- **Beauce** : Chartres, Orléans, Châteaudun
- **Bretagne** : Rennes, Brest, Vannes
- **Autres régions** : Lyon, Moulins, Tulle, Béziers, Aix-en-Provence, Pau

## 📡 Endpoints API principaux

- `GET /api/charts/monthly` - Données mensuelles (précipitations/températures)
- `GET /api/charts/options` - Villes et membres d'ensemble disponibles
- `POST /api/charts/cover-crop-feasibility` - Faisabilité des couverts végétaux
- `POST /api/charts/corn-viability` - Viabilité du maïs
- `GET /api/variables` - Variables climatiques disponibles
- `GET /api/experiments` - Scénarios climatiques disponibles
- `POST /api/dev/sql` - Requêtes SQL directes (mode développement)

Voir la documentation complète sur http://localhost:8000/docs

## 🚢 Déploiement

### Backend (Railway)
Le backend est déployé sur Railway avec Docker. Voir `Dockerfile` pour les détails.

### Frontend (Surge.sh)
Le frontend est déployé sur Surge.sh :
```bash
cd frontend
yarn build
surge dist/ agroclimavisio.surge.sh
```

## 📄 Licence

Voir le fichier LICENSE pour plus de détails.
