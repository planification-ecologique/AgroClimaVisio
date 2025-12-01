# AgroClimaVisio Backend

Backend FastAPI pour AgroClimaVisio.

## Prérequis

- Python 3.9+
- Poetry (voir [installation](https://python-poetry.org/docs/#installation))

## Installation

1. Installer Poetry si ce n'est pas déjà fait :
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Installer les dépendances :
```bash
poetry install
```

## Démarrage

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Ou activer l'environnement virtuel Poetry :
```bash
poetry shell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur http://localhost:8000

## Documentation API

Une fois le serveur démarré, la documentation interactive est disponible sur :
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Données de base
- `GET /` - Informations de base de l'API
- `GET /health` - Vérification de santé
- `GET /api/presets` - Liste des presets agricoles
- `GET /api/years` - Années disponibles pour les projections

### Métadonnées des données climatiques
- `GET /api/variables` - Liste des variables climatiques disponibles
- `GET /api/experiments` - Liste des scénarios climatiques disponibles
- `GET /api/datasets` - Liste des jeux de données avec filtres optionnels
- `GET /api/datasets/summary` - Résumé statistique des données

### Données de carte
- `POST /api/maps/data` - Récupération des données de carte (utilise les données réelles si disponibles, sinon mockées)

## Configuration

Créez un fichier `.env` dans le répertoire `backend/` :

```env
# Chemin vers les données NetCDF (optionnel)
CLIMATE_DATA_DIR=/chemin/vers/donnees/climatiques

# Configuration API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

## Données climatiques

Par défaut, l'API utilise des données mockées pour le développement. Pour utiliser les données réelles :

1. Téléchargez les fichiers NetCDF depuis data.gouv.fr
2. Configurez `CLIMATE_DATA_DIR` dans votre `.env`
3. L'API détectera automatiquement les fichiers

Voir `CLIMATE_DATA_SETUP.md` pour plus de détails.

## Structure du code

- `main.py` - Point d'entrée FastAPI et endpoints
- `models.py` - Modèles de données Pydantic pour les projections climatiques
- `datasets.py` - Catalogue des jeux de données disponibles
- `climate_data.py` - Chargeur de données NetCDF
- `indicators.py` - Calcul des indicateurs agro-climatiques

## Commandes Poetry utiles

- `poetry add <package>` - Ajouter une dépendance
- `poetry add --group dev <package>` - Ajouter une dépendance de développement
- `poetry remove <package>` - Supprimer une dépendance
- `poetry update` - Mettre à jour les dépendances
- `poetry show` - Afficher les dépendances installées
- `poetry lock` - Mettre à jour le fichier de lock

## TODO

- [x] Structure de base de l'API
- [x] Modèles de données pour les projections climatiques
- [x] Catalogue des jeux de données disponibles
- [x] Chargeur de données NetCDF
- [x] Calcul des indicateurs agro-climatiques
- [ ] Intégration complète avec les fichiers NetCDF réels
- [ ] Cache pour améliorer les performances
- [ ] Agrégation spatiale vers polygones administratifs
- [ ] Support de plusieurs modèles climatiques
