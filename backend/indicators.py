"""
Calcul des indicateurs agro-climatiques à partir des données climatiques
"""

from typing import Dict, Optional
from datetime import date
import xarray as xr
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon

from models import VariableType, ExperimentType
from climate_data import ClimateDataLoader, ClimateIndicatorCalculator


class AgroClimateIndicators:
    """Calcule les indicateurs agro-climatiques pour AgroClimaVisio"""
    
    def __init__(self, data_loader: ClimateDataLoader):
        """
        Initialise le calculateur d'indicateurs.
        
        Args:
            data_loader: Instance de ClimateDataLoader pour charger les données
        """
        self.data_loader = data_loader
        self.calculator = ClimateIndicatorCalculator()
    
    def calculate_potential_indicator(
        self,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        start_date: date,
        end_date: date,
        min_rainfall: float,
        min_rainfall_probability: float,
        degree_days_threshold: float,
        max_hot_days_30: int,
        member: str = "r1"
    ) -> Optional[xr.DataArray]:
        """
        Calcule l'indicateur de potentiel agro-climatique.
        
        Le potentiel est calculé comme une combinaison de :
        - Pluie minimale atteinte avec probabilité suffisante
        - Degrés-jours suffisants
        - Nombre de jours chauds acceptable
        
        Returns:
            DataArray avec les valeurs de potentiel (0-100%)
        """
        # Charger les données nécessaires
        pr_data = self.data_loader.get_data_for_period(
            VariableType.PR, experiment, gcm, rcm, start_date, end_date, member
        )
        tas_data = self.data_loader.get_data_for_period(
            VariableType.TAS, experiment, gcm, rcm, start_date, end_date, member
        )
        tasmax_data = self.data_loader.get_data_for_period(
            VariableType.TASMAX, experiment, gcm, rcm, start_date, end_date, member
        )
        
        if pr_data is None or tas_data is None or tasmax_data is None:
            return None
        
        # Calculer les indicateurs individuels
        total_rainfall = self.calculator.calculate_rainfall_total(
            pr_data, start_date, end_date
        )
        degree_days = self.calculator.calculate_degree_days(tas_data)
        hot_days_30 = self.calculator.calculate_hot_days(tasmax_data, threshold=30.0)
        
        # Normaliser chaque critère (0-1)
        # Pluie : 1 si >= min_rainfall, sinon proportionnel
        rainfall_score = xr.where(
            total_rainfall >= min_rainfall,
            1.0,
            total_rainfall / min_rainfall
        )
        rainfall_score = rainfall_score.clip(min=0, max=1)
        
        # Degrés-jours : 1 si >= threshold, sinon proportionnel
        degree_days_score = xr.where(
            degree_days >= degree_days_threshold,
            1.0,
            degree_days / degree_days_threshold
        )
        degree_days_score = degree_days_score.clip(min=0, max=1)
        
        # Jours chauds : 1 si <= max_hot_days_30, sinon pénalité
        hot_days_score = xr.where(
            hot_days_30 <= max_hot_days_30,
            1.0,
            xr.maximum(0, 1 - (hot_days_30 - max_hot_days_30) / max_hot_days_30)
        )
        hot_days_score = hot_days_score.clip(min=0, max=1)
        
        # Combinaison pondérée (moyenne simple pour l'instant)
        potential = (rainfall_score + degree_days_score + hot_days_score) / 3 * 100
        
        return potential
    
    def calculate_drought_risk(
        self,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        start_date: date,
        end_date: date,
        consecutive_dry_days_threshold: int,
        member: str = "r1"
    ) -> Optional[xr.DataArray]:
        """
        Calcule le risque de sécheresse prolongée.
        
        Returns:
            DataArray avec le nombre de jours consécutifs sans pluie
        """
        pr_data = self.data_loader.get_data_for_period(
            VariableType.PR, experiment, gcm, rcm, start_date, end_date, member
        )
        
        if pr_data is None:
            return None
        
        consecutive_dry = self.calculator.calculate_consecutive_dry_days(pr_data)
        
        return consecutive_dry
    
    def calculate_excess_water_risk(
        self,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        start_date: date,
        end_date: date,
        max_7day_rainfall_threshold: float,
        non_workable_days_threshold: int,
        member: str = "r1"
    ) -> Optional[xr.DataArray]:
        """
        Calcule le risque d'excès d'eau.
        
        Returns:
            DataArray avec un score de risque (0-100)
        """
        pr_data = self.data_loader.get_data_for_period(
            VariableType.PR, experiment, gcm, rcm, start_date, end_date, member
        )
        
        if pr_data is None:
            return None
        
        max_7day = self.calculator.calculate_7day_rainfall_max(pr_data)
        non_workable = self.calculator.calculate_non_workable_days(pr_data)
        
        # Score combiné
        risk_7day = xr.where(
            max_7day > max_7day_rainfall_threshold,
            (max_7day - max_7day_rainfall_threshold) / max_7day_rainfall_threshold * 50,
            0
        )
        
        risk_days = xr.where(
            non_workable > non_workable_days_threshold,
            (non_workable - non_workable_days_threshold) / non_workable_days_threshold * 50,
            0
        )
        
        total_risk = (risk_7day + risk_days).clip(min=0, max=100)
        
        return total_risk
    
    def calculate_heat_waves(
        self,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        start_date: date,
        end_date: date,
        threshold_35: int,
        member: str = "r1"
    ) -> Optional[xr.DataArray]:
        """
        Calcule le nombre de jours avec vagues de chaleur.
        
        Returns:
            DataArray avec le nombre de jours > 35°C
        """
        tasmax_data = self.data_loader.get_data_for_period(
            VariableType.TASMAX, experiment, gcm, rcm, start_date, end_date, member
        )
        
        if tasmax_data is None:
            return None
        
        hot_days_35 = self.calculator.calculate_hot_days(tasmax_data, threshold=35.0)
        
        return hot_days_35
    
    def dataarray_to_geojson(
        self,
        data_array: xr.DataArray,
        bbox: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Convertit un DataArray xarray en GeoJSON FeatureCollection.
        
        Args:
            data_array: DataArray avec les données à convertir
            bbox: Bounding box optionnel {"min_lon": ..., "max_lon": ..., "min_lat": ..., "max_lat": ...}
        
        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        
        # Vérifier que le DataArray n'est pas vide
        if data_array.size == 0:
            print("⚠️  DataArray vide, aucun feature à créer")
            return {
                "type": "FeatureCollection",
                "features": []
            }
        
        print(f"📊 Conversion DataArray vers GeoJSON: shape={data_array.shape}, size={data_array.size}")
        
        # Extraire les coordonnées
        if 'lat' in data_array.coords and 'lon' in data_array.coords:
            # Convertir en arrays numpy 1D pour éviter les problèmes
            lats = np.asarray(data_array.coords['lat'].values).flatten()
            lons = np.asarray(data_array.coords['lon'].values).flatten()
            
            # Filtrer par bbox si fourni
            if bbox:
                lats = lats[(lats >= bbox['min_lat']) & (lats <= bbox['max_lat'])]
                lons = lons[(lons >= bbox['min_lon']) & (lons <= bbox['max_lon'])]
            
            # Fonction helper pour convertir numpy arrays en float
            def to_float(val):
                """Convertit une valeur numpy en float Python"""
                # Si c'est déjà un scalaire Python
                if isinstance(val, (int, float)):
                    return float(val)
                
                # Si c'est un array numpy
                if hasattr(val, 'item'):
                    try:
                        return float(val.item())
                    except ValueError:
                        # Si item() échoue, essayer d'indexer
                        pass
                
                # Si c'est un array avec une seule valeur
                if hasattr(val, '__len__'):
                    if len(val) == 1:
                        return float(val[0])
                    elif len(val) > 1:
                        # Prendre le premier élément si array multi-dimensionnel
                        return float(val.flat[0]) if hasattr(val, 'flat') else float(val[0])
                
                # Dernier recours: conversion directe
                try:
                    return float(val)
                except (ValueError, TypeError):
                    # Si tout échoue, essayer de prendre le premier élément
                    if hasattr(val, '__getitem__'):
                        return float(val[0])
                    raise
            
            # Créer une grille de polygones
            for i in range(len(lats)):
                for j in range(len(lons)):
                    # Convertir en float dès le début pour éviter les problèmes avec numpy arrays
                    lat_val = to_float(lats[i])
                    lon_val = to_float(lons[j])
                    
                    # Calculer la taille de la cellule (approximative)
                    if i < len(lats) - 1:
                        next_lat_val = to_float(lats[i+1])
                        lat_step_val = abs(next_lat_val - lat_val) / 2
                    else:
                        prev_lat_val = to_float(lats[i-1]) if i > 0 else lat_val
                        lat_step_val = abs(lat_val - prev_lat_val) / 2 if i > 0 else 0.05
                    
                    if j < len(lons) - 1:
                        next_lon_val = to_float(lons[j+1])
                        lon_step_val = abs(next_lon_val - lon_val) / 2
                    else:
                        prev_lon_val = to_float(lons[j-1]) if j > 0 else lon_val
                        lon_step_val = abs(lon_val - prev_lon_val) / 2 if j > 0 else 0.05
                    
                    polygon = Polygon([
                        [lon_val - lon_step_val, lat_val - lat_step_val],
                        [lon_val + lon_step_val, lat_val - lat_step_val],
                        [lon_val + lon_step_val, lat_val + lat_step_val],
                        [lon_val - lon_step_val, lat_val + lat_step_val],
                        [lon_val - lon_step_val, lat_val - lat_step_val]
                    ])
                    
                    # Extraire la valeur (utiliser lat_val et lon_val qui sont des floats)
                    try:
                        value_data = data_array.sel(lat=lat_val, lon=lon_val, method='nearest')
                        # Gérer les cas où c'est un array
                        if hasattr(value_data, 'values'):
                            value_scalar = value_data.values
                            # Si c'est un array numpy, utiliser .item() pour obtenir un scalaire
                            if hasattr(value_scalar, 'item'):
                                value = float(value_scalar.item())
                            elif hasattr(value_scalar, '__len__') and len(value_scalar) == 1:
                                value = float(value_scalar[0])
                            else:
                                value = float(value_scalar)
                        else:
                            value = float(value_data)
                        if np.isnan(value):
                            continue
                    except (KeyError, IndexError, ValueError, TypeError) as e:
                        continue
                    
                    # Convertir les coordonnées du polygone en listes de floats
                    coords = [[float(c[0]), float(c[1])] for c in polygon.exterior.coords]
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [coords]
                        },
                        "properties": {
                            "value": round(value, 2),
                            "lat": lat_val,
                            "lon": lon_val
                        }
                    }
                    features.append(feature)
        else:
            print("⚠️  Coordonnées 'lat' ou 'lon' non trouvées dans le DataArray")
            print(f"   Coordonnées disponibles: {list(data_array.coords.keys())}")
        
        print(f"✅ Conversion terminée: {len(features)} features créées")
        
        return {
            "type": "FeatureCollection",
            "features": features
        }

