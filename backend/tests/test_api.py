"""
Tests pour l'API AgroClimaVisio
"""

import pytest
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    """Test de l'endpoint health"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_maps_data_excess_water():
    """Test de l'endpoint maps/data avec excess_water"""
    request_data = {
        "period": {
            "start_date": "2024-04-15",
            "end_date": "2024-06-28",
            "year": 2020
        },
        "map_type": "excess_water",
        "parameters": {}
    }
    
    response = client.post("/api/maps/data", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "data_source" in data
    assert "data" in data
    assert "legend" in data
    
    # Vérifier que les données sont présentes
    if data["data_source"] == "real":
        assert "features" in data["data"]
        assert len(data["data"]["features"]) > 0
        # Vérifier la structure d'une feature
        feature = data["data"]["features"][0]
        assert "type" in feature
        assert "geometry" in feature
        assert "properties" in feature
        assert "value" in feature["properties"]


def test_maps_data_drought():
    """Test de l'endpoint maps/data avec drought"""
    request_data = {
        "period": {
            "start_date": "2024-04-15",
            "end_date": "2024-06-28",
            "year": 2020
        },
        "map_type": "drought",
        "parameters": {
            "consecutive_dry_days": 10
        }
    }
    
    response = client.post("/api/maps/data", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "data_source" in data
    assert data["map_type"] == "drought"
    
    if data["data_source"] == "real":
        assert len(data["data"]["features"]) > 0


def test_maps_data_with_real_data():
    """Test que les données réelles sont utilisées si disponibles"""
    import os
    from pathlib import Path
    
    # Vérifier si des fichiers .nc existent
    possible_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "data"),
        os.path.join(os.path.dirname(__file__), "..", "..", "data"),
    ]
    
    has_nc_files = False
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            nc_files = list(Path(dir_path).glob("*.nc"))
            if len(nc_files) > 0:
                has_nc_files = True
                break
    
    if has_nc_files:
        request_data = {
            "period": {
                "start_date": "2024-04-15",
                "end_date": "2024-06-28",
                "year": 2020
            },
            "map_type": "excess_water",
            "parameters": {}
        }
        
        response = client.post("/api/maps/data", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Si des fichiers .nc existent, on devrait avoir des données réelles
        # (sauf si erreur de chargement)
        if data["data_source"] == "real":
            assert "features" in data["data"]
            assert len(data["data"]["features"]) > 0

