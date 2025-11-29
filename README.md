# AgroClimaVisio

AgroClimaVisio est une interface de visualisation agro‑climatique permettant aux agriculteurs, coopératives, conseillers et chercheurs de comprendre l'évolution du climat à l'échelle locale, pour mieux anticiper les risques (sécheresse, excès d'eau, orages violents) et optimiser les décisions agronomiques.

## 🚀 Technologies

- **Frontend**: Vite + React + TypeScript + MapLibre GL
- **Backend**: FastAPI (Python)
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
├── frontend/          # Application React + Vite
│   ├── src/
│   │   ├── components/  # Composants React
│   │   ├── types.ts     # Types TypeScript
│   │   └── App.tsx      # Composant principal
│   ├── package.json
│   └── yarn.lock
├── backend/           # API FastAPI
│   ├── main.py        # Point d'entrée de l'API
│   ├── pyproject.toml # Configuration Poetry
│   └── requirements.txt (optionnel, pour référence)
└── README.md
```

## 🎯 Fonctionnalités

- **Visualisation cartographique** interactive avec MapLibre
- **Paramètres ajustables** pour différents scénarios agricoles
- **Presets agricoles** (post-semis été, interculture été/hiver, semis blé)
- **Comparaison temporelle** (2020, 2030, 2040, 2050)
- **Types de cartes** :
  - Potentiel agro-climatique
  - Risque de sécheresse
  - Risque d'excès d'eau
  - Extrêmes (orages, chaleur)
  - Vagues de chaleur

## 🔧 Configuration

### Variables d'environnement

**Frontend** (`frontend/.env`):
```
VITE_API_URL=http://localhost:8000
```

**Backend** (`backend/.env`):
```
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

## 📝 TODO

- [ ] Intégrer les données climatiques de Météo-France
- [ ] Implémenter le calcul des indicateurs agro-climatiques
- [ ] Ajouter les couches de données sur la carte MapLibre
- [ ] Implémenter le mode comparaison
- [ ] Ajouter l'export de cartes
- [ ] Améliorer la gestion des erreurs
- [ ] Ajouter des tests

## 📄 Licence

Voir le fichier LICENSE pour plus de détails.
