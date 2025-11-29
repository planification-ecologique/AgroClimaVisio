from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

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


@app.post("/api/maps/data")
async def get_map_data(request: MapRequest):
    """
    Endpoint pour récupérer les données de carte selon les paramètres.
    Pour l'instant, retourne des données mockées.
    """
    # TODO: Implémenter la logique de récupération des données climatiques
    # depuis les projections Météo-France
    
    return {
        "map_type": request.map_type,
        "period": request.period.dict(),
        "parameters": request.parameters.dict(),
        "data": {
            "type": "FeatureCollection",
            "features": []
        },
        "legend": {
            "min": 0,
            "max": 100,
            "unit": "mm"
        }
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

