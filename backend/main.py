from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import random
import math

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
    Retourne des données mockées pour le développement.
    """
    # TODO: Implémenter la logique de récupération des données climatiques
    # depuis les projections Météo-France
    
    # Générer des données mockées
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
        "legend": legend
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

