from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from pathlib import Path
import random
import math

from models import (
    VariableType, ExperimentType, VARIABLES_INFO, VariableInfo
)
from datasets import (
    AVAILABLE_DATASETS, get_datasets_for_variables, 
    get_datasets_for_experiment, get_datasets_for_period
)
from points_config import get_all_points

app = FastAPI(title="AgroClimaVisio API", version="1.0.0")

# CORS middleware pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Port par défaut de Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Modèles de données
class PeriodRequest(BaseModel):
    start_date: str  # Format: "YYYY-MM-DD"
    end_date: str
    year: int  # 2020, 2030, 2040, 2050


class ClimateParameters(BaseModel):
    min_rainfall: Optional[float] = None  # mm
    min_rainfall_probability: Optional[float] = None  # 0-1
    degree_days_threshold: Optional[float] = None  # Degrés-jours
    degree_days_probability: Optional[float] = None
    max_hot_days_30: Optional[int] = None  # Jours > 30°C
    max_hot_days_35: Optional[int] = None  # Jours > 35°C
    hot_days_probability: Optional[float] = None
    consecutive_dry_days: Optional[int] = None  # Jours consécutifs sans pluie
    extreme_rainfall_threshold: Optional[float] = None  # mm en 30 min
    max_7day_rainfall: Optional[float] = None  # mm sur 7 jours
    non_workable_days_threshold: Optional[int] = None  # Jours avec pluie > 2mm


class MapRequest(BaseModel):
    period: PeriodRequest
    map_type: str  # "potential", "drought", "excess_water", "extremes", "heat_waves"
    parameters: ClimateParameters


@app.get("/")
async def root():
    return {"message": "AgroClimaVisio API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# Initialiser le chargeur DuckDB une seule fois au démarrage
_duckdb_loader = None

def get_duckdb_loader():
    """Obtient ou crée le chargeur DuckDB"""
    global _duckdb_loader
    if _duckdb_loader is None:
        try:
            from duckdb_loader import DuckDBClimateLoader
            db_path = Path(__file__).parent / "climate_data.duckdb"
            if db_path.exists():
                _duckdb_loader = DuckDBClimateLoader(db_path=str(db_path))
            else:
                print(f"⚠️  Base de données DuckDB non trouvée: {db_path}")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'initialisation de DuckDB: {e}")
    return _duckdb_loader


class MonthlyRainfallRequest(BaseModel):
    """Requête pour obtenir les données de pluie mensuelle"""
    start_date: str  # Format: "YYYY-MM-DD"
    end_date: str    # Format: "YYYY-MM-DD"
    experiment: Optional[str] = "ssp370"  # Par défaut ssp370
    gcm: Optional[str] = None  # Si None, utilise tous les GCM disponibles
    rcm: Optional[str] = None  # Si None, utilise tous les RCM disponibles


@app.post("/api/rainfall/monthly")
async def get_monthly_rainfall(request: MonthlyRainfallRequest):
    """
    Récupère les données de somme de pluie mensuelle pour les 6 points représentatifs
    (3 points Beauce + 3 points Bretagne) sur une période donnée.
    
    Retourne les données agrégées par mois pour chaque point.
    """
    loader = get_duckdb_loader()
    if loader is None:
        return {
            "error": "Base de données DuckDB non disponible",
            "points": []
        }
    
    try:
        from models import VariableType, ExperimentType
        
        # Convertir les dates (gérer les cas où c'est déjà un objet date ou une chaîne)
        if isinstance(request.start_date, str):
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        elif isinstance(request.start_date, date):
            start_date = request.start_date
        else:
            start_date = datetime.fromisoformat(str(request.start_date)).date()
        
        if isinstance(request.end_date, str):
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()
        elif isinstance(request.end_date, date):
            end_date = request.end_date
        else:
            end_date = datetime.fromisoformat(str(request.end_date)).date()
        
        # Convertir l'expérience
        experiment_map = {
            "historical": ExperimentType.HISTORICAL,
            "ssp370": ExperimentType.SSP370,
            "ssp585": ExperimentType.SSP585,
            "ssp245": ExperimentType.SSP245,
            "ssp126": ExperimentType.SSP126,
        }
        experiment = experiment_map.get(request.experiment.lower(), ExperimentType.SSP370)
        
        # Points représentatifs depuis la configuration centralisée
        all_points = get_all_points(format="dict")
        
        # Construire la requête SQL pour obtenir les sommes mensuelles
        # Les valeurs sont stockées telles quelles depuis NetCDF
        # Pour les précipitations, elles peuvent être en kg/m²/s ou mm/jour selon le fichier
        # On fait SUM pour obtenir le total mensuel
        # Si les valeurs sont en kg/m²/s, on multiplie par 86400 pour convertir en mm/jour avant SUM
        # Sinon, on suppose qu'elles sont déjà en mm/jour
        query = """
            SELECT 
                lat,
                lon,
                EXTRACT(YEAR FROM time) as year,
                EXTRACT(MONTH FROM time) as month,
                SUM(value * 86400) as monthly_total,
                COUNT(*) as days_count
            FROM climate_data
            WHERE variable = 'pr'
              AND experiment = ?
              AND time >= ?
              AND time <= ?
        """
        
        params = [experiment.value, start_date, end_date]
        
        # Ajouter filtres GCM/RCM si spécifiés
        if request.gcm:
            query += " AND gcm = ?"
            params.append(request.gcm)
        
        if request.rcm:
            query += " AND rcm = ?"
            params.append(request.rcm)
        
        # Filtrer pour les points spécifiques (avec tolérance de 0.1 degré)
        # Optimisation: utiliser une condition combinée pour meilleure performance
        point_conditions = []
        for point in all_points:
            point_conditions.append(f"(ABS(lat - {point['lat']}) < 0.1 AND ABS(lon - {point['lon']}) < 0.1)")
        
        query += f" AND ({' OR '.join(point_conditions)})"
        
        query += """
            GROUP BY lat, lon, year, month
            ORDER BY lat, lon, year, month
        """
        
        result_df = loader.conn.execute(query, params).df()
        
        if result_df.empty:
            return {
                "error": "Aucune donnée trouvée pour cette période",
                "points": []
            }
        
        # Convertir en format JSON pour le frontend
        # Grouper par point et créer les séries temporelles
        data_by_point = {}
        
        for _, row in result_df.iterrows():
            # Trouver le point le plus proche
            point_key = None
            min_dist = float('inf')
            for point in all_points:
                dist = abs(row['lat'] - point['lat']) + abs(row['lon'] - point['lon'])
                if dist < min_dist:
                    min_dist = dist
                    point_key = point['name']
            
            if point_key not in data_by_point:
                data_by_point[point_key] = {
                    "name": point_key,
                    "lat": float(row['lat']),
                    "lon": float(row['lon']),
                    "data": []
                }
            
            # Les valeurs sont stockées en mm/jour dans DuckDB (déjà converties lors de l'import)
            # SUM donne le total mensuel en mm
            monthly_total_mm = float(row['monthly_total'])
            
            data_by_point[point_key]["data"].append({
                "year": int(row['year']),
                "month": int(row['month']),
                "date": f"{int(row['year'])}-{int(row['month']):02d}-01",
                "value": round(monthly_total_mm, 2),
                "days_count": int(row['days_count'])
            })
        
        # Convertir en liste et trier
        result_data = list(data_by_point.values())
        for point_data in result_data:
            point_data["data"].sort(key=lambda x: (x["year"], x["month"]))
        
        return {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "experiment": request.experiment,
            "points": result_data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "points": []
        }


# Initialiser le chargeur DuckDB une seule fois au démarrage
_duckdb_loader = None

def get_duckdb_loader():
    """Obtient ou crée le chargeur DuckDB"""
    global _duckdb_loader
    if _duckdb_loader is None:
        from duckdb_loader import DuckDBClimateLoader
        db_path = Path(__file__).parent / "climate_data.duckdb"
        if db_path.exists():
            _duckdb_loader = DuckDBClimateLoader(db_path=str(db_path))
        else:
            print(f"⚠️  Base de données DuckDB non trouvée: {db_path}")
    return _duckdb_loader


def generate_mock_geojson(map_type: str, center_lon: float = 1.4437, center_lat: float = 43.6047):
    """
    Génère des données GeoJSON mockées autour d'un point central (Toulouse par défaut).
    Crée une grille de polygones avec des valeurs simulées selon le type de carte.
    """
    features = []
    grid_size = 5  # 5x5 grille
    cell_size = 0.1  # Taille de chaque cellule en degrés
    
    # Valeurs de base selon le type de carte
    base_values = {
        "potential": {"min": 30, "max": 90, "unit": "%"},
        "drought": {"min": 0, "max": 45, "unit": "jours"},
        "excess_water": {"min": 0, "max": 80, "unit": "mm"},
        "extremes": {"min": 0, "max": 25, "unit": "événements"},
        "heat_waves": {"min": 0, "max": 20, "unit": "jours"}
    }
    
    config = base_values.get(map_type, {"min": 0, "max": 100, "unit": ""})
    
    for i in range(grid_size):
        for j in range(grid_size):
            # Position de la cellule
            lon_offset = (i - grid_size / 2) * cell_size
            lat_offset = (j - grid_size / 2) * cell_size
            
            # Coordonnées du centre de la cellule
            cell_lon = center_lon + lon_offset
            cell_lat = center_lat + lat_offset
            
            # Valeur simulée avec variation spatiale
            # Créer un pattern réaliste avec variation graduelle
            distance_from_center = math.sqrt(lon_offset**2 + lat_offset**2)
            base_value = config["min"] + (config["max"] - config["min"]) * (1 - distance_from_center / (grid_size * cell_size / 2))
            value = base_value + random.uniform(-10, 10)
            value = max(config["min"], min(config["max"], value))  # Clamp entre min et max
            
            # Créer un polygone carré pour la cellule
            half_cell = cell_size / 2
            coordinates = [[
                [cell_lon - half_cell, cell_lat - half_cell],
                [cell_lon + half_cell, cell_lat - half_cell],
                [cell_lon + half_cell, cell_lat + half_cell],
                [cell_lon - half_cell, cell_lat + half_cell],
                [cell_lon - half_cell, cell_lat - half_cell]
            ]]
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coordinates
                },
                "properties": {
                    "value": round(value, 1),
                    "cell_id": f"{i}_{j}"
                }
            }
            features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


@app.post("/api/maps/data")
async def get_map_data(request: MapRequest):
    """
    Endpoint pour récupérer les données de carte selon les paramètres.
    Essaie de charger les données réelles, sinon retourne des données mockées.
    """
    import os
    from datetime import datetime
    from climate_data import ClimateDataLoader
    from indicators import AgroClimateIndicators
    
    # Essayer de charger les données réelles
    # Chercher dans plusieurs emplacements possibles
    possible_dirs = [
        os.getenv("CLIMATE_DATA_DIR"),  # Variable d'environnement (priorité)
        os.path.join(os.path.dirname(__file__), "data"),  # backend/data/
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),  # ./data/ à la racine
    ]
    
    # Vérifier que le répertoire existe ET contient des fichiers .nc
    use_real_data = False
    data_directory = None
    
    for dir_path in possible_dirs:
        if not dir_path:
            continue
        if os.path.exists(dir_path):
            nc_files = list(Path(dir_path).glob("*.nc"))
            print(f"🔍 Vérification: {dir_path} -> {len(nc_files)} fichiers .nc")
            if len(nc_files) > 0:
                data_directory = dir_path
                use_real_data = True
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Données réelles trouvées: {len(nc_files)} fichier(s) dans {data_directory}")
                print(f"✅ Données réelles trouvées: {len(nc_files)} fichier(s) dans {data_directory}")
                break
    
    if not use_real_data:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("⚠️  Aucun fichier .nc trouvé. Utilisation des données mockées.")
        logger.info("💡 Placez vos fichiers .nc dans backend/data/ ou ./data/")
        print("⚠️  Aucun fichier .nc trouvé. Utilisation des données mockées.")
        print(f"💡 Répertoires vérifiés: {possible_dirs}")
    
    if use_real_data:
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔄 Tentative de chargement des données réelles depuis {data_directory}")
            print(f"🔄 Tentative de chargement des données réelles depuis {data_directory}")
            
            loader = ClimateDataLoader(data_directory)
            indicators = AgroClimateIndicators(loader)
            
            # Convertir les dates et ajuster à l'année de la requête
            # Les dates de la requête peuvent être dans une année différente (ex: 2024)
            # mais on veut les données pour l'année spécifiée (ex: 2020)
            original_start = datetime.strptime(request.period.start_date, "%Y-%m-%d").date()
            original_end = datetime.strptime(request.period.end_date, "%Y-%m-%d").date()
            
            # Ajuster les dates à l'année de la requête
            start_date = original_start.replace(year=request.period.year)
            end_date = original_end.replace(year=request.period.year)
            
            logger.info(f"📅 Dates ajustées: {start_date} à {end_date} (année: {request.period.year})")
            print(f"📅 Dates ajustées: {start_date} à {end_date} (année: {request.period.year})")
            
            # Déterminer le scénario selon l'année
            if request.period.year <= 2014:
                experiment = ExperimentType.HISTORICAL
            else:
                experiment = ExperimentType.SSP370  # Par défaut
            
            logger.info(f"🔬 Scénario sélectionné: {experiment.value} pour l'année {request.period.year}")
            print(f"🔬 Scénario sélectionné: {experiment.value} pour l'année {request.period.year}")
            
            # Utiliser un modèle par défaut (peut être paramétrable plus tard)
            gcm = "CNRM-ESM2-1"
            rcm = "CNRM-ALADIN64E1"
            member = "r1"
            
            # Calculer l'indicateur selon le type de carte
            if request.map_type == "potential":
                result = indicators.calculate_potential_indicator(
                    experiment, gcm, rcm, start_date, end_date,
                    request.parameters.min_rainfall or 80,
                    request.parameters.min_rainfall_probability or 0.8,
                    request.parameters.degree_days_threshold or 500,
                    request.parameters.max_hot_days_30 or 10,
                    member
                )
            elif request.map_type == "drought":
                result = indicators.calculate_drought_risk(
                    experiment, gcm, rcm, start_date, end_date,
                    request.parameters.consecutive_dry_days or 10,
                    member
                )
            elif request.map_type == "excess_water":
                result = indicators.calculate_excess_water_risk(
                    experiment, gcm, rcm, start_date, end_date,
                    request.parameters.max_7day_rainfall or 40,
                    request.parameters.non_workable_days_threshold or 7,
                    member
                )
            elif request.map_type == "heat_waves":
                result = indicators.calculate_heat_waves(
                    experiment, gcm, rcm, start_date, end_date,
                    request.parameters.max_hot_days_35 or 5,
                    member
                )
            else:
                result = None
                print(f"⚠️  Type de carte non géré: {request.map_type}")
            
            if result is not None:
                print(f"✅ Résultat calculé avec succès pour {request.map_type}")
                # Convertir en GeoJSON
                geojson_data = indicators.dataarray_to_geojson(result)
                
                # Calculer min/max pour la légende
                values = [f["properties"]["value"] for f in geojson_data["features"]]
                legend = {
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 100,
                    "unit": "%" if request.map_type == "potential" else "jours" if request.map_type in ["drought", "heat_waves"] else "mm"
                }
                
                return {
                    "map_type": request.map_type,
                    "period": request.period.dict(),
                    "parameters": request.parameters.dict(),
                    "data": geojson_data,
                    "legend": legend,
                    "data_source": "real"
                }
            else:
                print(f"⚠️  Résultat None pour {request.map_type}, basculement vers mock")
        except Exception as e:
            # En cas d'erreur, utiliser les données mockées
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur lors du chargement des données réelles: {e}")
            logger.debug(traceback.format_exc())
            logger.info("🔄 Basculement vers les données mockées")
            print(f"❌ Erreur lors du chargement des données réelles: {e}")
            print(traceback.format_exc())
            print("🔄 Basculement vers les données mockées")
    
    # Générer des données mockées (fallback)
    mock_data = generate_mock_geojson(request.map_type)
    
    # Déterminer la légende selon le type de carte
    legend_configs = {
        "potential": {"min": 0, "max": 100, "unit": "%"},
        "drought": {"min": 0, "max": 50, "unit": "jours"},
        "excess_water": {"min": 0, "max": 100, "unit": "mm"},
        "extremes": {"min": 0, "max": 30, "unit": "événements"},
        "heat_waves": {"min": 0, "max": 25, "unit": "jours"}
    }
    
    legend = legend_configs.get(request.map_type, {"min": 0, "max": 100, "unit": ""})
    
    return {
        "map_type": request.map_type,
        "period": request.period.dict(),
        "parameters": request.parameters.dict(),
        "data": mock_data,
        "legend": legend,
        "data_source": "mock"
    }


@app.get("/api/presets")
async def get_presets():
    """
    Retourne les presets agricoles disponibles.
    """
    return {
        "presets": [
            {
                "id": "post_semis_ete",
                "name": "Post-semis été",
                "start_date": "2024-04-15",
                "end_date": "2024-06-30"
            },
            {
                "id": "interculture_ete",
                "name": "Interculture été",
                "start_date": "2024-07-01",
                "end_date": "2024-09-15"
            },
            {
                "id": "interculture_hiver",
                "name": "Interculture hiver",
                "start_date": "2024-09-16",
                "end_date": "2024-11-30"
            },
            {
                "id": "semis_ble",
                "name": "Semis blé",
                "start_date": "2024-10-01",
                "end_date": "2024-11-15"
            }
        ]
    }


@app.get("/api/years")
async def get_available_years():
    """
    Retourne les années disponibles pour les projections.
    """
    return {
        "years": [2020, 2030, 2040, 2050],
        "current": 2020
    }


@app.get("/api/variables")
async def get_available_variables():
    """
    Retourne la liste des variables climatiques disponibles.
    """
    variables = [
        {
            "code": var.code.value,
            "name": var.name,
            "unit": var.unit,
            "description": var.description
        }
        for var in VARIABLES_INFO.values()
    ]
    return {"variables": variables}


@app.get("/api/experiments")
async def get_available_experiments():
    """
    Retourne la liste des scénarios climatiques disponibles.
    """
    experiment_names = {
        ExperimentType.HISTORICAL: "Données historiques",
        ExperimentType.SSP126: "SSP1-2.6 (Scénario optimiste)",
        ExperimentType.SSP245: "SSP2-4.5 (Scénario intermédiaire)",
        ExperimentType.SSP370: "SSP3-7.0 (Scénario pessimiste)",
        ExperimentType.SSP585: "SSP5-8.5 (Scénario très pessimiste)"
    }
    
    experiments = [
        {"code": exp.value, "name": experiment_names.get(exp, exp.value)}
        for exp in ExperimentType
    ]
    return {"experiments": experiments}


@app.get("/api/datasets")
async def get_available_datasets(
    variable: Optional[str] = None,
    experiment: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
):
    """
    Retourne la liste des jeux de données disponibles avec filtres optionnels.
    
    Paramètres:
    - variable: Filtrer par variable (ex: "pr", "tas")
    - experiment: Filtrer par scénario (ex: "ssp370", "historical")
    - start_year: Année de début de la période
    - end_year: Année de fin de la période
    """
    datasets = AVAILABLE_DATASETS.copy()
    
    if variable:
        try:
            var_type = VariableType(variable)
            datasets = get_datasets_for_variables([var_type])
        except ValueError:
            return {"error": f"Variable '{variable}' non reconnue"}
    
    if experiment:
        try:
            exp_type = ExperimentType(experiment)
            datasets = [ds for ds in datasets if exp_type in ds.experiment]
        except ValueError:
            return {"error": f"Scénario '{experiment}' non reconnu"}
    
    if start_year and end_year:
        datasets = [ds for ds in datasets 
                   if ds.period_start <= start_year and ds.period_end >= end_year]
    
    return {
        "datasets": [
            {
                "gcm": ds.gcm.value,
                "rcm": ds.rcm.value,
                "experiments": [e.value for e in ds.experiment],
                "variables": [v.value for v in ds.variables],
                "resolution": ds.resolution,
                "period": f"{ds.period_start}-{ds.period_end}",
                "frequency": ds.frequency,
                "member": ds.member,
                "downscaling_method": ds.downscaling_method.value
            }
            for ds in datasets
        ],
        "count": len(datasets)
    }


@app.get("/api/datasets/summary")
async def get_datasets_summary():
    """
    Retourne un résumé des données disponibles.
    """
    total_datasets = len(AVAILABLE_DATASETS)
    variables_available = set()
    experiments_available = set()
    resolutions_available = set()
    
    for ds in AVAILABLE_DATASETS:
        variables_available.update([v.value for v in ds.variables])
        experiments_available.update([e.value for e in ds.experiment])
        resolutions_available.add(ds.resolution)
    
    return {
        "total_datasets": total_datasets,
        "variables_count": len(variables_available),
        "variables": sorted(list(variables_available)),
        "experiments_count": len(experiments_available),
        "experiments": sorted(list(experiments_available)),
        "resolutions": sorted(list(resolutions_available)),
        "data_url": "https://console.object.files.data.gouv.fr/browser/meteofrance-drias/SocleM-Climat-2025%2F",
        "documentation_url": "https://guides.data.gouv.fr/guide-du-participant-au-hackathon-le-climat-en-donnees/ressources-du-hackathon/donnees/donnees-de-projections-climatiques"
    }

