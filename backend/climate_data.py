"""
Module pour charger et traiter les données climatiques NetCDF
"""

try:
    import xarray as xr
    import numpy as np
    XARRAY_AVAILABLE = True
except ImportError:
    XARRAY_AVAILABLE = False
    xr = None
    np = None

from typing import Optional, Dict, List, Tuple
from datetime import datetime, date
from pathlib import Path
import logging

try:
    from models import VariableType, ExperimentType, ClimateDataset
except ImportError:
    # Fallback pour les imports - définir des types de base si nécessaire
    from enum import Enum
    class VariableType(Enum):
        PR = "pr"
        TAS = "tas"
        TASMAX = "tasmax"
        TASMIN = "tasmin"
        RSDS = "rsds"
        RLDS = "rlds"
        HUSS = "huss"
        SFCWIND = "sfcWind"
    
    class ExperimentType(Enum):
        HISTORICAL = "historical"
        SSP370 = "ssp370"
        SSP585 = "ssp585"
        SSP245 = "ssp245"
        SSP126 = "ssp126"

logger = logging.getLogger(__name__)


class ClimateDataLoader:
    """Chargeur de données climatiques depuis les fichiers NetCDF"""
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialise le chargeur de données.
        
        Args:
            data_directory: Chemin vers le répertoire contenant les fichiers NetCDF
        """
        self.data_directory = Path(data_directory) if data_directory else None
        self._cache: Dict[str, xr.Dataset] = {}
    
    def load_dataset(
        self,
        variable: VariableType,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        member: str = "r1",
        year: Optional[int] = None
    ):
        """
        Charge un jeu de données climatiques depuis un fichier NetCDF.
        
        Args:
            variable: Variable climatique à charger
            experiment: Scénario climatique
            gcm: Modèle climatique global
            rcm: Modèle climatique régional
            member: Membre d'ensemble (ex: "r1")
            year: Année spécifique (optionnel, sinon charge toute la période)
        
        Returns:
            Dataset xarray ou None si le fichier n'existe pas
        """
        if not XARRAY_AVAILABLE:
            logger.warning("xarray n'est pas installé. Installez-le avec: poetry install")
            return None
        # Construire le nom de fichier selon la convention Météo-France
        # Format réel: {variable}Adjusted_FR-Metro_{GCM}_{scenario}_{member}_CNRM-MF_{RCM}_v1-r1_MF-CDFt-SAFRAN-1985-2014_day_{dates}.nc
        cache_key = f"{variable.value}_{experiment.value}_{gcm}_{rcm}_{member}"
        
        if cache_key in self._cache:
            logger.info(f"Chargement depuis le cache: {cache_key}")
            return self._cache[cache_key]
        
        if not self.data_directory or not self.data_directory.exists():
            logger.warning(f"Répertoire de données non disponible: {self.data_directory}")
            return None
        
        # Mapper les variables aux noms de fichiers réels
        # Les fichiers peuvent utiliser "prAdjust" ou "prAdjusted"
        variable_map = {
            VariableType.PR: ["prAdjust", "prAdjusted"],
            VariableType.TAS: ["tasAdjust", "tasAdjusted"],
            VariableType.TASMAX: ["tasmaxAdjust", "tasmaxAdjusted"],
            VariableType.TASMIN: ["tasminAdjust", "tasminAdjusted"],
            VariableType.RSDS: ["rsdsAdjust", "rsdsAdjusted"],
            VariableType.RLDS: ["rldsAdjust", "rldsAdjusted"],
            VariableType.HUSS: ["hussAdjust", "hussAdjusted"],
            VariableType.SFCWIND: ["sfcWindAdjust", "sfcWindAdjusted"]
        }
        
        # Mapper les scénarios (les fichiers utilisent "ssp370" dans le nom, pas "p370")
        scenario_map = {
            ExperimentType.HISTORICAL: ["historical"],
            ExperimentType.SSP370: ["ssp370", "p370"],
            ExperimentType.SSP585: ["ssp585", "p585"],
            ExperimentType.SSP245: ["ssp245", "p245"],
            ExperimentType.SSP126: ["ssp126", "p126"]
        }
        
        var_names = variable_map.get(variable, [variable.value])
        scenario_names = scenario_map.get(experiment, [experiment.value])
        
        # Chercher le fichier avec plusieurs patterns possibles
        # Les fichiers peuvent être directement dans data_directory ou dans une structure de dossiers
        file_patterns = []
        
        # Patterns pour fichiers directement dans le répertoire (cas actuel)
        # Format réel: prAdjust_FR-Metro_CNRM-ESM2-1_ssp370_r1i1p1f2_CNRM-MF_CNRM-ALADIN64E1_*.nc
        for var_name in var_names:
            for scenario_name in scenario_names:
                # Pattern exact avec scénario dans le nom
                file_patterns.append(f"**/{var_name}_*{scenario_name}*{gcm}*{rcm}*.nc")
                # Pattern avec membre (r1i1p1f2 pour r1)
                member_pattern = member.replace("r", "r") + "i1p1f2" if member.startswith("r") else member
                file_patterns.append(f"**/{var_name}_*{scenario_name}*{member_pattern}*.nc")
                # Pattern plus large (sans contraintes strictes)
                file_patterns.append(f"**/*{var_name}*{scenario_name}*.nc")
        
        # Patterns pour structure de dossiers complète (si organisés différemment)
        for var_name in var_names:
            for scenario_name in scenario_names:
                file_patterns.append(f"**/{gcm}/{member}*/{rcm}/{scenario_name}/day/{var_name}/version-hackathon-*/{var_name}_*.nc")
                file_patterns.append(f"**/{gcm}/*/{rcm}/{scenario_name}/*/{var_name}*/*.nc")
        
        file_path = None
        for pattern in file_patterns:
            matches = list(self.data_directory.glob(pattern))
            if matches:
                file_path = matches[0]
                logger.info(f"Fichier trouvé avec pattern '{pattern}': {file_path}")
                print(f"✅ Fichier trouvé: {file_path}")
                break
        
        if not file_path or not file_path.exists():
            logger.warning(f"Fichier non trouvé pour {cache_key}")
            print(f"❌ Fichier non trouvé pour variable={variable.value}, experiment={experiment.value}, gcm={gcm}, rcm={rcm}")
            print(f"   Répertoire cherché: {self.data_directory}")
            print(f"   Patterns testés: {file_patterns[:3]}...")
            return None
        
        try:
            logger.info(f"Chargement du fichier: {file_path}")
            ds = xr.open_dataset(file_path)
            
            # Sélectionner l'année si spécifiée
            if year and 'time' in ds.coords:
                ds = ds.sel(time=f"{year}")
            
            # Mettre en cache
            self._cache[cache_key] = ds
            
            return ds
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path}: {e}")
            return None
    
    def get_data_for_period(
        self,
        variable: VariableType,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        start_date: date,
        end_date: date,
        member: str = "r1"
    ):
        """
        Récupère les données pour une période spécifique.
        
        Args:
            variable: Variable climatique
            experiment: Scénario climatique
            gcm: Modèle climatique global
            rcm: Modèle climatique régional
            start_date: Date de début
            end_date: Date de fin
            member: Membre d'ensemble
        
        Returns:
            DataArray xarray avec les données pour la période
        """
        ds = self.load_dataset(variable, experiment, gcm, rcm, member)
        
        if ds is None:
            return None
        
        # Sélectionner la période
        if 'time' in ds.coords:
            try:
                time_slice = slice(start_date.isoformat(), end_date.isoformat())
                selected = ds.sel(time=time_slice)
                
                # Vérifier que la sélection a retourné des données
                if len(selected.time) == 0:
                    logger.warning(f"Aucune donnée trouvée pour la période {start_date} à {end_date}")
                    print(f"⚠️  Aucune donnée trouvée pour la période {start_date} à {end_date}")
                    # Afficher la plage de dates disponible
                    time_coords = ds.coords['time']
                    if len(time_coords) > 0:
                        first_date = str(time_coords.values[0])[:10] if hasattr(time_coords.values[0], '__str__') else str(time_coords.values[0])
                        last_date = str(time_coords.values[-1])[:10] if hasattr(time_coords.values[-1], '__str__') else str(time_coords.values[-1])
                        logger.info(f"📅 Plage disponible dans le fichier: {first_date} à {last_date}")
                        print(f"📅 Plage disponible dans le fichier: {first_date} à {last_date}")
                    return None
                
                ds = selected
                logger.info(f"✅ Données sélectionnées: {len(ds.time)} pas de temps pour {start_date} à {end_date}")
                print(f"✅ Données sélectionnées: {len(ds.time)} pas de temps")
            except Exception as e:
                logger.error(f"Erreur lors de la sélection temporelle: {e}")
                print(f"❌ Erreur lors de la sélection temporelle: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Extraire la variable
        # Les fichiers utilisent des noms comme "prAdjust", "prAdjusted", "pr", etc.
        variable_map = {
            VariableType.PR: ["prAdjust", "prAdjusted", "pr", "precipitation"],
            VariableType.TAS: ["tasAdjust", "tasAdjusted", "tas", "temperature"],
            VariableType.TASMAX: ["tasmaxAdjust", "tasmaxAdjusted", "tasmax", "temperature_max"],
            VariableType.TASMIN: ["tasminAdjust", "tasminAdjusted", "tasmin", "temperature_min"],
            VariableType.RSDS: ["rsdsAdjust", "rsdsAdjusted", "rsds", "solar_radiation"],
            VariableType.RLDS: ["rldsAdjust", "rldsAdjusted", "rlds", "longwave_radiation"],
            VariableType.HUSS: ["hussAdjust", "hussAdjusted", "huss", "specific_humidity"],
            VariableType.SFCWIND: ["sfcWindAdjust", "sfcWindAdjusted", "sfcWind", "wind_speed"]
        }
        
        var_names = variable_map.get(variable, [variable.value])
        
        for var_name in var_names:
            if var_name in ds.data_vars:
                return ds[var_name]
            elif var_name in ds.coords:
                return ds.coords[var_name]
        
        # Si aucune correspondance, essayer de trouver la première variable de données
        if len(ds.data_vars) > 0:
            first_var = list(ds.data_vars.keys())[0]
            logger.warning(f"Variable {variable.value} non trouvée, utilisation de {first_var}")
            return ds[first_var]
        
        logger.warning(f"Variable {variable.value} non trouvée dans le dataset. Variables disponibles: {list(ds.data_vars.keys())}")
        return None


class ClimateIndicatorCalculator:
    """Calcule les indicateurs agro-climatiques à partir des données brutes"""
    
    @staticmethod
    def calculate_rainfall_total(
        precipitation,
        start_date: date,
        end_date: date
    ):
        """
        Calcule le cumul de précipitations sur une période.
        
        Args:
            precipitation: DataArray avec les précipitations (kg/m²/s)
            start_date: Date de début
            end_date: Date de fin
        
        Returns:
            Cumul de précipitations en mm
        """
        # Convertir de kg/m²/s à mm
        # 1 kg/m²/s = 1 mm/s (pour l'eau)
        # Multiplier par le nombre de secondes dans une journée (86400) pour avoir mm/jour
        if 'time' in precipitation.coords:
            period_data = precipitation.sel(time=slice(start_date.isoformat(), end_date.isoformat()))
        else:
            period_data = precipitation
        
        # Somme sur la période
        total = period_data.sum(dim='time') * 86400  # Conversion en mm
        
        return total
    
    @staticmethod
    def calculate_consecutive_dry_days(
        precipitation,
        threshold: float = 0.1  # mm/jour
    ):
        """
        Calcule le nombre maximum de jours consécutifs sans pluie.
        
        Args:
            precipitation: DataArray avec les précipitations (kg/m²/s)
            threshold: Seuil de précipitation en mm/jour
        
        Returns:
            Nombre maximum de jours consécutifs sans pluie
        """
        # Convertir en mm/jour
        pr_mm = precipitation * 86400
        
        # Identifier les jours secs (< threshold)
        dry_days = pr_mm < threshold
        
        # Calculer les séquences consécutives
        max_consecutive = xr.zeros_like(pr_mm.isel(time=0))
        
        for lat_idx in range(pr_mm.sizes.get('lat', 0)):
            for lon_idx in range(pr_mm.sizes.get('lon', 0)):
                if 'lat' in pr_mm.coords and 'lon' in pr_mm.coords:
                    point_data = dry_days.isel(lat=lat_idx, lon=lon_idx)
                else:
                    point_data = dry_days
                
                # Trouver la séquence la plus longue
                max_seq = 0
                current_seq = 0
                
                for day in point_data.values:
                    if day:
                        current_seq += 1
                        max_seq = max(max_seq, current_seq)
                    else:
                        current_seq = 0
                
                if 'lat' in max_consecutive.coords and 'lon' in max_consecutive.coords:
                    max_consecutive.isel(lat=lat_idx, lon=lon_idx).values[:] = max_seq
                else:
                    max_consecutive.values[:] = max_seq
        
        return max_consecutive
    
    @staticmethod
    def calculate_hot_days(
        temperature_max,
        threshold: float = 30.0  # °C
    ):
        """
        Calcule le nombre de jours avec température maximale > seuil.
        
        Args:
            temperature_max: DataArray avec températures maximales (K)
            threshold: Seuil de température en °C
        
        Returns:
            Nombre de jours > seuil
        """
        # Convertir de Kelvin à Celsius
        temp_celsius = temperature_max - 273.15
        
        # Compter les jours > seuil
        hot_days = (temp_celsius > threshold).sum(dim='time')
        
        return hot_days
    
    @staticmethod
    def calculate_degree_days(
        temperature_mean,
        base_temperature: float = 0.0  # °C
    ):
        """
        Calcule la somme des degrés-jours.
        
        Args:
            temperature_mean: DataArray avec températures moyennes (K)
            base_temperature: Température de base en °C
        
        Returns:
            Somme des degrés-jours
        """
        # Convertir de Kelvin à Celsius
        temp_celsius = temperature_mean - 273.15
        
        # Calculer les degrés-jours (max(0, T - T_base))
        degree_days = xr.where(
            temp_celsius > base_temperature,
            temp_celsius - base_temperature,
            0
        )
        
        # Somme sur la période
        total_degree_days = degree_days.sum(dim='time')
        
        return total_degree_days
    
    @staticmethod
    def calculate_7day_rainfall_max(
        precipitation,
        window_size: int = 7
    ):
        """
        Calcule le maximum de précipitations cumulées sur une fenêtre glissante.
        
        Args:
            precipitation: DataArray avec les précipitations (kg/m²/s)
            window_size: Taille de la fenêtre en jours
        
        Returns:
            Maximum des cumuls sur fenêtre glissante en mm
        """
        # Convertir en mm/jour
        pr_mm = precipitation * 86400
        
        # Calculer la moyenne glissante
        rolling_sum = pr_mm.rolling(time=window_size, center=False).sum()
        
        # Maximum sur toute la période
        max_7day = rolling_sum.max(dim='time')
        
        return max_7day
    
    @staticmethod
    def calculate_non_workable_days(
        precipitation,
        threshold: float = 2.0  # mm/jour
    ):
        """
        Calcule le nombre de jours non praticables (pluie > seuil).
        
        Args:
            precipitation: DataArray avec les précipitations (kg/m²/s)
            threshold: Seuil de précipitation en mm/jour
        
        Returns:
            Nombre de jours avec pluie > seuil
        """
        # Convertir en mm/jour
        pr_mm = precipitation * 86400
        
        # Compter les jours > seuil
        non_workable = (pr_mm > threshold).sum(dim='time')
        
        return non_workable

