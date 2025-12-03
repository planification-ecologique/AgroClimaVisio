from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from pathlib import Path
import random
import math
import os
import pandas as pd

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
# Permet les origines depuis les variables d'environnement ou localhost par défaut
default_origins = "http://localhost:5173,https://agroclimavisio.surge.sh,http://agroclimavisio.surge.sh"
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", default_origins).split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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


@app.on_event("startup")
async def startup_event():
    """Initialise le loader DuckDB au démarrage de l'application"""
    print("🚀 Démarrage de l'application...")
    # Initialiser DuckDB en arrière-plan pour ne pas bloquer le démarrage
    import asyncio
    async def init_duckdb():
        try:
            loader = get_duckdb_loader()
            if loader:
                print("✅ Loader DuckDB initialisé avec succès au démarrage")
            else:
                print("⚠️  Loader DuckDB non disponible au démarrage (sera initialisé à la première requête)")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'initialisation au démarrage: {e}")
            print("⚠️  L'application continuera sans DuckDB (sera initialisé à la première requête)")
    
    # Lancer l'initialisation en arrière-plan sans attendre
    asyncio.create_task(init_duckdb())
    print("✅ Application démarrée (initialisation DuckDB en cours en arrière-plan)")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug/db")
async def debug_db():
    """Endpoint de debug pour vérifier l'état de la base de données"""
    global _duckdb_init_error
    debug_info = {
        "current_directory": os.getcwd(),
        "file_parent": str(Path(__file__).parent),
        "duckdb_path_env": os.getenv("DUCKDB_PATH"),
        "possible_paths": [],
        "found_path": None,
        "loader_available": _duckdb_loader is not None,
        "init_error": _duckdb_init_error
    }
    
    # Liste des chemins possibles
    possible_paths = []
    if os.getenv("DUCKDB_PATH"):
        possible_paths.append(Path(os.getenv("DUCKDB_PATH")) / "climate_data.duckdb")
    possible_paths.append(Path(__file__).parent / "data" / "climate_data.duckdb")
    possible_paths.append(Path("/app/backend/data/climate_data.duckdb"))
    possible_paths.append(Path("backend/data/climate_data.duckdb"))
    possible_paths.append(Path("data/climate_data.duckdb"))
    
    for path in possible_paths:
        exists = path.exists()
        debug_info["possible_paths"].append({
            "path": str(path),
            "exists": exists,
            "is_file": path.is_file() if exists else False,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2) if exists and path.is_file() else None
        })
        if exists and debug_info["found_path"] is None:
            debug_info["found_path"] = str(path)
    
    return debug_info


# Initialiser le chargeur DuckDB une seule fois au démarrage
_duckdb_loader = None
_duckdb_init_error = None

def get_duckdb_loader():
    """Obtient ou crée le chargeur DuckDB"""
    global _duckdb_loader, _duckdb_init_error
    if _duckdb_loader is None:
        try:
            from duckdb_loader import DuckDBClimateLoader
            
            # Liste des chemins possibles à vérifier (dans l'ordre de priorité)
            possible_paths = []
            
            # 1. Variable d'environnement DUCKDB_PATH (Volume Railway)
            if os.getenv("DUCKDB_PATH"):
                possible_paths.append(Path(os.getenv("DUCKDB_PATH")) / "climate_data.duckdb")
            
            # 2. backend/data/ (développement local et Railway par défaut)
            possible_paths.append(Path(__file__).parent / "data" / "climate_data.duckdb")
            
            # 3. Chemin absolu /app/backend/data/ (Railway)
            possible_paths.append(Path("/app/backend/data/climate_data.duckdb"))
            
            # 4. Chemin relatif depuis le répertoire courant
            possible_paths.append(Path("backend/data/climate_data.duckdb"))
            possible_paths.append(Path("data/climate_data.duckdb"))
            
            # Chercher le premier chemin qui existe
            db_path = None
            for path in possible_paths:
                if path.exists():
                    db_path = path
                    print(f"✅ Base de données DuckDB trouvée: {db_path}")
                    break
            
            if db_path is None:
                print("⚠️  Base de données DuckDB non trouvée. Chemins vérifiés:")
                for path in possible_paths:
                    print(f"   - {path} (existe: {path.exists()})")
                print(f"   Répertoire courant: {os.getcwd()}")
                print(f"   __file__ parent: {Path(__file__).parent}")
                print(f"   DUCKDB_PATH env: {os.getenv('DUCKDB_PATH')}")
            else:
                try:
                    print(f"🔄 Initialisation du loader DuckDB avec: {db_path}")
                    _duckdb_loader = DuckDBClimateLoader(db_path=str(db_path))
                    print("✅ Loader DuckDB initialisé avec succès")
                    _duckdb_init_error = None  # Réinitialiser l'erreur en cas de succès
                except Exception as loader_error:
                    _duckdb_init_error = str(loader_error)
                    print(f"❌ Erreur lors de l'initialisation du loader DuckDB: {loader_error}")
                    import traceback
                    traceback.print_exc()
                    # Ne pas lever l'exception, on veut que l'API démarre même sans DB
        except Exception as e:
            _duckdb_init_error = str(e)
            print(f"⚠️  Erreur lors de l'initialisation de DuckDB: {e}")
            import traceback
            traceback.print_exc()
            # Ne pas lever l'exception ici, on veut que l'API démarre même sans DB
            # Le loader sera None et les endpoints retourneront une erreur appropriée
    return _duckdb_loader


class MonthlyChartRequest(BaseModel):
    """Requête pour obtenir les données climatiques mensuelles"""
    start_date: str  # Format: "YYYY-MM-DD"
    end_date: str    # Format: "YYYY-MM-DD"
    experiment: Optional[str] = "ssp370"  # Par défaut ssp370
    variable: str = "pr"  # Variable climatique: "pr" (précipitations) ou "tas" (température)
    gcm: Optional[str] = None  # Si None, utilise tous les GCM disponibles
    rcm: Optional[str] = None  # Si None, utilise tous les RCM disponibles
    cities: Optional[List[str]] = None  # Liste des villes à inclure (ex: ["Chartres", "Rennes"])
    members: Optional[List[str]] = None  # Liste des membres d'ensemble (ex: ["r1", "r2"])


class CoverCropFeasibilityRequest(BaseModel):
    """Requête pour calculer la faisabilité des couverts végétaux"""
    city: str  # Ville pour laquelle calculer la faisabilité
    start_year: int = 1990
    end_year: int = 2100
    experiment: Optional[str] = "ssp370"


class CornViabilityRequest(BaseModel):
    """Requête pour calculer la viabilité du maïs"""
    city: str  # Ville pour laquelle calculer la viabilité
    start_year: int = 1990
    end_year: int = 2100
    experiment: Optional[str] = "ssp370"
    # Seuils configurables (seront appliqués côté frontend, mais on peut les prévoir ici pour documentation)


class SQLQueryRequest(BaseModel):
    """Requête SQL libre (développement uniquement)"""
    query: str  # Requête SQL à exécuter


@app.post("/api/charts/monthly")
async def get_monthly_chart_data(request: MonthlyChartRequest):
    """
    Récupère les données climatiques mensuelles pour les points représentatifs
    sur une période donnée.
    
    Variables supportées:
    - "pr": Précipitations (somme mensuelle en mm)
    - "tas": Température (moyenne mensuelle en °C)
    
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
        
        # Filtrer les points par villes si spécifiées
        if request.cities and len(request.cities) > 0:
            # Convertir en minuscules pour comparaison insensible à la casse
            cities_lower = [c.lower() for c in request.cities]
            all_points = [p for p in all_points if p['name'].lower() in cities_lower]
        
        if not all_points:
            return {
                "error": "Aucun point trouvé pour les villes sélectionnées",
                "points": []
            }
        
        # Valider la variable
        if request.variable not in ['pr', 'tas']:
            return {
                "error": f"Variable non supportée: {request.variable}. Utilisez 'pr' ou 'tas'.",
                "points": []
            }
        
        # Construire la requête SQL selon la variable
        # IMPORTANT: Grouper par gcm/rcm/member pour éviter le double comptage
        # Filtrer uniquement les données EMUL
        if request.variable == 'pr':
            # Précipitations: somme mensuelle (convertir kg/m²/s en mm)
            aggregation = "SUM(value * 86400) as monthly_total"
        else:  # tas
            # Température: moyenne mensuelle (convertir Kelvin en Celsius)
            # Les données sont stockées en Kelvin, on soustrait 273.15 pour obtenir °C
            aggregation = "AVG(value - 273.15) as monthly_avg"
        
        query = f"""
            SELECT 
                lat,
                lon,
                gcm,
                rcm,
                member,
                EXTRACT(YEAR FROM time) as year,
                EXTRACT(MONTH FROM time) as month,
                {aggregation},
                COUNT(*) as days_count
            FROM climate_data
            WHERE variable = ?
              AND experiment = ?
              AND time >= ?
              AND time <= ?
              AND (rcm LIKE '%EMUL%' OR rcm LIKE '%emul%' OR rcm = 'CNRM-ALADIN63-EMUL')
        """
        
        params = [request.variable, experiment.value, start_date, end_date]
        
        # Ajouter filtres GCM/RCM si spécifiés
        if request.gcm:
            query += " AND gcm = ?"
            params.append(request.gcm)
        
        if request.rcm:
            query += " AND rcm = ?"
            params.append(request.rcm)
        
        # Filtrer par membres d'ensemble si spécifiés
        if request.members and len(request.members) > 0:
            # Créer une liste de placeholders pour les membres
            member_placeholders = ','.join(['?' for _ in request.members])
            query += f" AND member IN ({member_placeholders})"
            params.extend(request.members)
        
        # Filtrer pour les points spécifiques (avec tolérance de 0.1 degré)
        # Optimisation: utiliser une condition combinée pour meilleure performance
        point_conditions = []
        for point in all_points:
            point_conditions.append(f"(ABS(lat - {point['lat']}) < 0.1 AND ABS(lon - {point['lon']}) < 0.1)")
        
        query += f" AND ({' OR '.join(point_conditions)})"
        
        query += """
            GROUP BY lat, lon, gcm, rcm, member, year, month
            ORDER BY lat, lon, gcm, rcm, member, year, month
        """
        
        result_df = loader.conn.execute(query, params).df()
        
        if result_df.empty:
            return {
                "error": "Aucune donnée trouvée pour cette période",
                "points": []
            }
        
        # Convertir en format JSON pour le frontend
        # Grouper par point ET par gcm/rcm pour éviter le double comptage
        # Si plusieurs gcm/rcm existent pour le même point/mois, on les garde séparés
        data_by_point_gcm_rcm = {}
        
        for _, row in result_df.iterrows():
            # Trouver le point le plus proche
            point_key = None
            min_dist = float('inf')
            for point in all_points:
                dist = abs(row['lat'] - point['lat']) + abs(row['lon'] - point['lon'])
                if dist < min_dist:
                    min_dist = dist
                    point_key = point['name']
            
            # Clé unique: point + gcm + rcm + member pour éviter le double comptage
            gcm = str(row['gcm'])
            rcm = str(row['rcm'])
            member = str(row['member'])
            unique_key = f"{point_key}_{gcm}_{rcm}_{member}"
            
            if unique_key not in data_by_point_gcm_rcm:
                data_by_point_gcm_rcm[unique_key] = {
                    "name": point_key,
                    "lat": float(row['lat']),
                    "lon": float(row['lon']),
                    "gcm": gcm,
                    "rcm": rcm,
                    "member": member,
                    "data": []
                }
            
            # Récupérer la valeur selon la variable
            if request.variable == 'pr':
                # Précipitations: valeur déjà convertie en mm
                value = float(row['monthly_total'])
            else:  # tas
                # Température: moyenne en °C
                value = float(row['monthly_avg'])
            
            data_by_point_gcm_rcm[unique_key]["data"].append({
                "year": int(row['year']),
                "month": int(row['month']),
                "date": f"{int(row['year'])}-{int(row['month']):02d}",
                "value": round(value, 2),
                "days_count": int(row['days_count'])
            })
        
        # Convertir en liste et trier
        # Chaque combinaison point/gcm/rcm/member aura sa propre série temporelle
        result_data = list(data_by_point_gcm_rcm.values())
        for point_data in result_data:
            point_data["data"].sort(key=lambda x: (x["year"], x["month"]))
            # Ajouter le nom avec gcm/rcm/member pour identification dans le frontend
            point_data["name"] = f"{point_data['name']} ({point_data['gcm']}/{point_data['rcm']}/{point_data['member']})"
        
        return {
            "start_date": request.start_date,
            "end_date": request.end_date,
            "experiment": request.experiment,
            "variable": request.variable,
            "points": result_data
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "points": []
        }


@app.post("/api/charts/cover-crop-feasibility")
async def get_cover_crop_feasibility(request: CoverCropFeasibilityRequest):
    """
    Calcule le % de membres EMUL qui vérifient le critère de faisabilité des couverts végétaux :
    - Minimum des fenêtres glissantes de précipitations sur la période
    - Résultat par année pour deux tailles de fenêtre (21 et 42 jours)
    """
    # Configuration des fenêtres glissantes
    window_sizes = [21, 42]  # Tailles de fenêtre en jours
    
    loader = get_duckdb_loader()
    if loader is None:
        return {
            "error": "Base de données DuckDB non disponible",
            "years": [],
            "success_percentages": []
        }
    
    try:
        from models import ExperimentType
        from points_config import get_point_by_name
        
        # Récupérer le point géographique
        try:
            point = get_point_by_name(request.city)
        except ValueError:
            return {
                "error": f"Ville non trouvée: {request.city}",
                "years": [],
                "success_percentages": []
            }
        
        # Convertir l'expérience
        experiment_map = {
            "historical": ExperimentType.HISTORICAL,
            "ssp370": ExperimentType.SSP370,
            "ssp585": ExperimentType.SSP585,
            "ssp245": ExperimentType.SSP245,
            "ssp126": ExperimentType.SSP126,
        }
        experiment = experiment_map.get(request.experiment.lower(), ExperimentType.SSP370)
        
        # Récupérer tous les membres EMUL disponibles
        members_df = loader.conn.execute("""
            SELECT DISTINCT member
            FROM climate_data
            WHERE (rcm LIKE '%EMUL%' OR rcm LIKE '%emul%' OR rcm = 'CNRM-ALADIN63-EMUL')
              AND experiment = ?
            ORDER BY member
        """, [experiment.value]).df()
        
        available_members = members_df['member'].tolist() if not members_df.empty else []
        
        if not available_members:
            return {
                "error": "Aucun membre EMUL trouvé",
                "years": [],
                "success_percentages": []
            }
        
        years = list(range(request.start_year, request.end_year + 1))
        
        # Pour chaque année, calculer le minimum des fenêtres glissantes pour chaque membre et chaque taille de fenêtre
        yearly_data = {}
        
        for year in years:
            # Période : 15 août au 15 octobre
            start_date = date(year, 8, 15)
            end_date = date(year, 10, 15)
            
            # Récupérer les données quotidiennes pour tous les membres
            query = """
                SELECT 
                    member,
                    time,
                    SUM(value * 86400) as daily_pr_mm  -- Convertir kg/m²/s en mm
                FROM climate_data
                WHERE variable = 'pr'
                  AND experiment = ?
                  AND time >= ?
                  AND time <= ?
                  AND (rcm LIKE '%EMUL%' OR rcm LIKE '%emul%' OR rcm = 'CNRM-ALADIN63-EMUL')
                  AND ABS(lat - ?) < 0.1
                  AND ABS(lon - ?) < 0.1
                GROUP BY member, time, lat, lon
                ORDER BY member, time
            """
            
            result_df = loader.conn.execute(
                query,
                [experiment.value, start_date, end_date, point['lat'], point['lon']]
            ).df()
            
            if result_df.empty:
                yearly_data[year] = {
                    "member_minima": {}
                }
                continue
            
            # Pour chaque taille de fenêtre, calculer le minimum pour chaque membre
            member_minima_by_window = {}
            
            for window_size in window_sizes:
                member_minima = {}
                
                for member in available_members:
                    member_data = result_df[result_df['member'] == member].copy()
                    
                    if member_data.empty:
                        member_minima[member] = None
                        continue
                    
                    # Convertir en datetime si nécessaire
                    if 'time' in member_data.columns:
                        member_data['time'] = pd.to_datetime(member_data['time'])
                        member_data = member_data.sort_values('time')
                    
                    # Calculer le minimum des fenêtres glissantes
                    daily_pr = member_data['daily_pr_mm'].values
                    
                    if len(daily_pr) < window_size:
                        member_minima[member] = None
                        continue
                    
                    # Fenêtres glissantes
                    window_sums = []
                    for i in range(len(daily_pr) - window_size + 1):
                        window_sum = sum(daily_pr[i:i+window_size])
                        window_sums.append(window_sum)
                    
                    if window_sums:
                        member_minima[member] = round(min(window_sums), 2)
                    else:
                        member_minima[member] = None
                
                member_minima_by_window[window_size] = member_minima
            
            yearly_data[year] = {
                "member_minima_by_window": member_minima_by_window
            }
        
        return {
            "city": request.city,
            "criterion": "Minimum des fenêtres glissantes (15 août - 15 octobre)",
            "window_sizes": window_sizes,
            "years": years,
            "yearly_data": yearly_data,
            "total_members": len(available_members),
            "members": available_members
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "years": [],
            "yearly_data": {}
        }


@app.post("/api/charts/corn-viability")
async def get_corn_viability(request: CornViabilityRequest):
    """
    Calcule le % de membres EMUL qui vérifient les critères de viabilité du maïs :
    - Semis : cumul minimum sur mars-avril
    - Croissance courbe 1 : minimum des fenêtres glissantes de 60j (mi-mai à fin août)
    - Croissance courbe 2 : minimum des fenêtres glissantes de 30j (mi-mai à fin août)
    - Récolte : minimum des fenêtres glissantes de 15j (mi-octobre à mi-décembre) <= seuil
    """
    loader = get_duckdb_loader()
    if loader is None:
        return {
            "error": "Base de données DuckDB non disponible",
            "years": [],
            "yearly_data": {}
        }
    
    try:
        from models import ExperimentType
        from points_config import get_point_by_name
        
        # Récupérer le point géographique
        try:
            point = get_point_by_name(request.city)
        except ValueError:
            return {
                "error": f"Ville non trouvée: {request.city}",
                "years": [],
                "yearly_data": {}
            }
        
        # Convertir l'expérience
        experiment_map = {
            "historical": ExperimentType.HISTORICAL,
            "ssp370": ExperimentType.SSP370,
            "ssp585": ExperimentType.SSP585,
            "ssp245": ExperimentType.SSP245,
            "ssp126": ExperimentType.SSP126,
        }
        experiment = experiment_map.get(request.experiment.lower(), ExperimentType.SSP370)
        
        # Récupérer tous les membres EMUL disponibles
        members_df = loader.conn.execute("""
            SELECT DISTINCT member
            FROM climate_data
            WHERE (rcm LIKE '%EMUL%' OR rcm LIKE '%emul%' OR rcm = 'CNRM-ALADIN63-EMUL')
              AND experiment = ?
            ORDER BY member
        """, [experiment.value]).df()
        
        available_members = members_df['member'].tolist() if not members_df.empty else []
        
        if not available_members:
            return {
                "error": "Aucun membre EMUL trouvé",
                "years": [],
                "yearly_data": {}
            }
        
        years = list(range(request.start_year, request.end_year + 1))
        yearly_data = {}
        
        for year in years:
            # Périodes pour chaque critère
            # Semis : mars-avril
            sowing_start = date(year, 3, 1)
            sowing_end = date(year, 4, 30)
            
            # Croissance : mi-mai à fin août
            growth_start = date(year, 5, 15)
            growth_end = date(year, 8, 31)
            
            # Récolte : mi-octobre à mi-décembre
            harvest_start = date(year, 10, 15)
            harvest_end = date(year, 12, 15)
            
            # Récupérer toutes les données nécessaires pour cette année
            # IMPORTANT: Grouper uniquement par member, time pour agréger toutes les cellules de grille
            query = """
                SELECT 
                    member,
                    time,
                    SUM(value * 86400) as daily_pr_mm
                FROM climate_data
                WHERE variable = 'pr'
                  AND experiment = ?
                  AND time >= ?
                  AND time <= ?
                  AND (rcm LIKE '%EMUL%' OR rcm LIKE '%emul%' OR rcm = 'CNRM-ALADIN63-EMUL')
                  AND ABS(lat - ?) < 0.1
                  AND ABS(lon - ?) < 0.1
                GROUP BY member, time
                ORDER BY member, time
            """
            
            # Utiliser la période la plus large pour récupérer toutes les données d'un coup
            all_period_start = sowing_start
            all_period_end = harvest_end
            
            result_df = loader.conn.execute(
                query,
                [experiment.value, all_period_start, all_period_end, point['lat'], point['lon']]
            ).df()
            
            if result_df.empty:
                yearly_data[year] = {
                    "sowing_totals": {},
                    "growth_minima_60d": {},
                    "growth_minima_30d": {},
                    "harvest_minima_15d": {}
                }
                continue
            
            # Pour chaque membre, calculer les indicateurs
            sowing_totals = {}
            growth_minima_60d = {}
            growth_minima_30d = {}
            harvest_minima_15d = {}
            
            for member in available_members:
                member_data = result_df[result_df['member'] == member].copy()
                
                if member_data.empty:
                    sowing_totals[member] = None
                    growth_minima_60d[member] = None
                    growth_minima_30d[member] = None
                    harvest_minima_15d[member] = None
                    continue
                
                # Convertir en datetime si nécessaire
                if 'time' in member_data.columns:
                    member_data['time'] = pd.to_datetime(member_data['time'])
                    member_data = member_data.sort_values('time')
                
                daily_pr = member_data['daily_pr_mm'].values
                dates = pd.to_datetime(member_data['time'].values)
                
                # 1. Semis : cumul sur mars-avril
                sowing_mask = (dates >= pd.Timestamp(sowing_start)) & (dates <= pd.Timestamp(sowing_end))
                sowing_pr = daily_pr[sowing_mask]
                if len(sowing_pr) > 0:
                    sowing_totals[member] = round(sum(sowing_pr), 2)
                else:
                    sowing_totals[member] = None
                
                # 2. Croissance courbe 1 : minimum des fenêtres glissantes de 60 jours
                growth_mask = (dates >= pd.Timestamp(growth_start)) & (dates <= pd.Timestamp(growth_end))
                growth_pr = daily_pr[growth_mask]
                if len(growth_pr) >= 60:
                    window_size = 60
                    window_sums = []
                    for i in range(len(growth_pr) - window_size + 1):
                        window_sum = sum(growth_pr[i:i+window_size])
                        window_sums.append(window_sum)
                    if window_sums:
                        growth_minima_60d[member] = round(min(window_sums), 2)
                    else:
                        growth_minima_60d[member] = None
                else:
                    growth_minima_60d[member] = None
                
                # 3. Croissance courbe 2 : minimum des fenêtres glissantes de 30 jours
                if len(growth_pr) >= 30:
                    window_size = 30
                    window_sums = []
                    for i in range(len(growth_pr) - window_size + 1):
                        window_sum = sum(growth_pr[i:i+window_size])
                        window_sums.append(window_sum)
                    if window_sums:
                        growth_minima_30d[member] = round(min(window_sums), 2)
                    else:
                        growth_minima_30d[member] = None
                else:
                    growth_minima_30d[member] = None
                
                # 4. Récolte : minimum des fenêtres glissantes de 15 jours (on veut le min pour vérifier qu'au moins une fenêtre <= seuil)
                harvest_mask = (dates >= pd.Timestamp(harvest_start)) & (dates <= pd.Timestamp(harvest_end))
                harvest_pr = daily_pr[harvest_mask]
                if len(harvest_pr) >= 15:
                    window_size = 15
                    window_sums = []
                    for i in range(len(harvest_pr) - window_size + 1):
                        window_sum = sum(harvest_pr[i:i+window_size])
                        window_sums.append(window_sum)
                    if window_sums:
                        harvest_minima_15d[member] = round(min(window_sums), 2)
                    else:
                        harvest_minima_15d[member] = None
                else:
                    harvest_minima_15d[member] = None
            
            yearly_data[year] = {
                "sowing_totals": sowing_totals,
                "growth_minima_60d": growth_minima_60d,
                "growth_minima_30d": growth_minima_30d,
                "harvest_minima_15d": harvest_minima_15d
            }
        
        return {
            "city": request.city,
            "criterion": "Viabilité du maïs (semis + croissance + récolte)",
            "years": years,
            "yearly_data": yearly_data,
            "total_members": len(available_members),
            "members": available_members
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "years": [],
            "yearly_data": {}
        }


@app.post("/api/dev/sql")
async def execute_sql_query(request: SQLQueryRequest):
    """
    Endpoint de développement pour exécuter des requêtes SQL directement.
    
    ⚠️ SÉCURITÉ : Disponible uniquement en développement/local.
    - Limité aux requêtes SELECT uniquement
    - Désactivé en production
    """
    # Vérifier que nous sommes en développement
    is_dev = os.getenv("ENVIRONMENT", "development").lower() in ["development", "dev", "local"]
    allow_sql = os.getenv("ALLOW_FREE_SQL", "false").lower() == "true"
    
    if not (is_dev or allow_sql):
        return {
            "error": "Cet endpoint n'est disponible qu'en développement. Définissez ALLOW_FREE_SQL=true pour l'activer.",
            "allowed": False
        }
    
    # Normaliser la requête
    query = request.query.strip()
    query_upper = query.upper().strip()
    
    # Vérifier que c'est une requête SELECT uniquement
    # if not query_upper.startswith("SELECT"):
    #     return {
    #         "error": "Seules les requêtes SELECT sont autorisées pour des raisons de sécurité.",
    #         "allowed": False
    #     }

    # Vérifier qu'il n'y a pas de commandes dangereuses
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {
                "error": f"Commande dangereuse détectée: {keyword}. Seules les requêtes SELECT sont autorisées.",
                "allowed": False
            }
    
    loader = get_duckdb_loader()
    if loader is None:
        return {
            "error": "Base de données DuckDB non disponible",
            "results": None
        }
    
    try:
        # Exécuter la requête
        result_df = loader.conn.execute(query).df()
        
        # Convertir en format JSON-friendly
        # Convertir les types numpy/pandas en types Python natifs
        result_dict = result_df.to_dict(orient='records')
        
        # Nettoyer les valeurs (convertir numpy types en Python types)
        cleaned_results = []
        for row in result_dict:
            cleaned_row = {}
            for key, value in row.items():
                # Gérer les types numpy/pandas
                if pd.isna(value):
                    cleaned_row[key] = None
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    cleaned_row[key] = str(value)
                elif hasattr(value, 'item'):  # numpy scalar
                    cleaned_row[key] = value.item()
                else:
                    cleaned_row[key] = value
            cleaned_results.append(cleaned_row)
        
        return {
            "query": query,
            "row_count": len(cleaned_results),
            "columns": list(result_df.columns) if not result_df.empty else [],
            "results": cleaned_results,
            "error": None
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            "query": query,
            "error": str(e),
            "traceback": error_trace if is_dev else None,  # Cacher la traceback en production
            "results": None
        }


@app.get("/api/charts/options")
async def get_charts_options():
    """
    Retourne les options disponibles pour les filtres (villes et membres d'ensemble).
    """
    loader = get_duckdb_loader()
    if loader is None:
        return {
            "error": "Base de données DuckDB non disponible",
            "cities": [],
            "members": []
        }
    
    try:
        # Récupérer toutes les villes disponibles depuis la configuration
        all_points = get_all_points(format="dict")
        cities = [{"name": p["name"], "region": p["region"]} for p in all_points]
        
        # Récupérer les membres d'ensemble disponibles depuis la base de données
        # (pour toutes les variables, pas seulement pr)
        members_df = loader.conn.execute("""
            SELECT DISTINCT member
            FROM climate_data
            WHERE (rcm LIKE '%EMUL%' OR rcm LIKE '%emul%' OR rcm = 'CNRM-ALADIN63-EMUL')
            ORDER BY member
        """).df()
        
        members = members_df['member'].tolist() if not members_df.empty else []
        
        return {
            "cities": cities,
            "members": members
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "cities": [],
            "members": []
        }


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

