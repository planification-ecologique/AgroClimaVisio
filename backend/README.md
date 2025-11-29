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

- `GET /` - Informations de base de l'API
- `GET /health` - Vérification de santé
- `GET /api/presets` - Liste des presets agricoles
- `GET /api/years` - Années disponibles pour les projections
- `POST /api/maps/data` - Récupération des données de carte

## Commandes Poetry utiles

- `poetry add <package>` - Ajouter une dépendance
- `poetry add --group dev <package>` - Ajouter une dépendance de développement
- `poetry remove <package>` - Supprimer une dépendance
- `poetry update` - Mettre à jour les dépendances
- `poetry show` - Afficher les dépendances installées
- `poetry export -f requirements.txt --output requirements.txt` - Exporter vers requirements.txt (si nécessaire)

## TODO

- [ ] Intégrer les données climatiques de Météo-France
- [ ] Implémenter le calcul des indicateurs agro-climatiques
- [ ] Ajouter le cache pour les requêtes fréquentes
- [ ] Ajouter l'authentification si nécessaire
