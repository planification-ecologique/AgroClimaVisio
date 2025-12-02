# DuckDB pour accès rapide aux données climatiques

## Installation

```bash
cd backend
poetry add duckdb pandas
poetry install
```

## Utilisation rapide

### 1. Importer les fichiers NetCDF dans DuckDB

```bash
# Utiliser poetry run pour exécuter dans l'environnement virtuel
poetry run python import_to_duckdb.py

# Ou activer l'environnement virtuel d'abord
poetry shell
python import_to_duckdb.py
```

Cela va :
- Créer une base de données `climate_data.duckdb`
- Importer tous les fichiers `.nc` du répertoire `data/`
- Créer les index pour accès rapide

**Temps estimé** : ~10-15 minutes par fichier de 2GB (optimisé pour mémoire)

**Mémoire requise** : ~200-500MB (au lieu de 4-8GB avant optimisation)

### 2. Utiliser la base de données

```python
from duckdb_loader import DuckDBClimateLoader
from models import VariableType, ExperimentType
from datetime import date

# Ouvrir la base
loader = DuckDBClimateLoader(db_path="climate_data.duckdb")

# Récupérer toutes les données pour un carré de grille
df = loader.get_data_for_grid_cell(
    lat=43.6047,  # Toulouse
    lon=1.4437,
    variables=[VariableType.PR, VariableType.TAS],
    experiment=ExperimentType.SSP370,
    gcm="CNRM-ESM2-1",
    rcm="CNRM-ALADIN64E1",
    member="r1",
    start_date=date(2020, 1, 1),
    end_date=date(2020, 12, 31)
)

print(df)
```

### 3. Exemples d'utilisation

```bash
poetry run python example_duckdb_usage.py
```

Voir `example_duckdb_usage.py` pour plus d'exemples.

## Avantages vs xarray

| Opération | xarray | DuckDB |
|-----------|--------|--------|
| Accès point par point | ⚠️ Scan complet | ✅ Index (10-100x plus rapide) |
| Agrégations temporelles | ⚠️ Chargement mémoire | ✅ SQL optimisé |
| Jointures multi-variables | ⚠️ Plusieurs fichiers | ✅ Une requête SQL |
| Requêtes complexes | ⚠️ Code Python | ✅ SQL natif |

## Structure de la base

```sql
CREATE TABLE climate_data (
    variable VARCHAR,      -- 'pr', 'tas', etc.
    experiment VARCHAR,    -- 'historical', 'ssp370', etc.
    gcm VARCHAR,          -- 'CNRM-ESM2-1', etc.
    rcm VARCHAR,          -- 'CNRM-ALADIN64E1', etc.
    member VARCHAR,       -- 'r1', etc.
    lat DOUBLE,           -- Latitude
    lon DOUBLE,           -- Longitude
    time DATE,            -- Date
    value DOUBLE          -- Valeur
);

-- Index pour performance
CREATE INDEX idx_spatial ON climate_data(lat, lon);
CREATE INDEX idx_temporal ON climate_data(time);
CREATE INDEX idx_variable ON climate_data(variable, experiment, gcm, rcm);
```

## Requêtes SQL personnalisées

Vous pouvez exécuter des requêtes SQL directement :

```python
# Moyennes mensuelles
result = loader.conn.execute("""
    SELECT 
        EXTRACT(YEAR FROM time) as year,
        EXTRACT(MONTH FROM time) as month,
        AVG(value) as avg_value
    FROM climate_data
    WHERE variable = 'pr'
      AND ABS(lat - 43.6) < 0.05
      AND ABS(lon - 1.4) < 0.05
    GROUP BY year, month
    ORDER BY year, month
""").df()
```

## Performance

Pour 4 datasets de ~2GB chacun :

- **Taille base DuckDB** : ~6-8GB (avec compression)
- **Temps d'import** : ~40-60 minutes total (optimisé mémoire)
- **Mémoire utilisée** : ~200-500MB (au lieu de 4-8GB avant optimisation)
- **Temps de requête point par point** : < 100ms
- **Temps d'agrégation annuelle** : < 500ms

### Optimisations mémoire

Le script a été optimisé pour traiter les données **pas de temps par pas de temps** au lieu de charger tout le fichier en mémoire. Si vous rencontrez encore des problèmes de mémoire, vous pouvez réduire `chunk_size` dans `import_netcdf_file()`.

Voir `docs/temp/MEMORY_OPTIMIZATION.md` pour plus de détails.

## Recommandation

✅ **Utilisez DuckDB si** :
- Vous faites principalement des analyses point par point
- Vous avez besoin de joindre plusieurs variables
- Vous faites beaucoup d'agrégations temporelles

⚠️ **Gardez xarray si** :
- Vous travaillez avec des régions entières
- Vous avez besoin d'opérations spatiales complexes (interpolation, régrillage)

## Solution hybride

Vous pouvez utiliser les deux :
- **DuckDB** pour analyses point par point et agrégations
- **xarray** pour visualisations de régions entières

