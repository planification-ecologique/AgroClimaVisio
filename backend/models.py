"""
Modèles de données pour les projections climatiques Météo-France SOCLE Métropole
Basé sur les données du hackathon "Le climat en données" 2025
"""

from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum


class ExperimentType(str, Enum):
    """Types d'expériences climatiques"""
    HISTORICAL = "historical"
    SSP126 = "ssp126"
    SSP245 = "ssp245"
    SSP370 = "ssp370"
    SSP585 = "ssp585"


class DownscalingMethod(str, Enum):
    """Méthodes de descente d'échelle"""
    RCM = "RCM"  # Regional Climate Model
    CPRCM = "CPRCM"  # Convection-Permitting Regional Climate Model
    EMULATEUR = "EMULATEUR"


class VariableType(str, Enum):
    """Variables climatiques disponibles"""
    TAS = "tas"  # Température moyenne à 2m (K)
    TASMIN = "tasmin"  # Température minimale à 2m (K)
    TASMAX = "tasmax"  # Température maximale à 2m (K)
    PR = "pr"  # Précipitations (kg/m2/s)
    RSDS = "rsds"  # Rayonnement solaire incident (W/m2)
    RLDS = "rlds"  # Rayonnement infrarouge incident (W/m2)
    HUSS = "huss"  # Humidité spécifique (kg/kg)
    SFCWIND = "sfcWind"  # Vitesse du vent à 10m (m/s)


class GCMType(str, Enum):
    """Modèles climatiques globaux (GCM)"""
    CNRM_ESM2_1 = "CNRM-ESM2-1"
    NORESM2_MM = "NorESM2-MM"
    CMCC_CM2_SR5 = "CMCC-CM2-SR5"
    IPSL_CM6A_LR = "IPSL-CM6A-LR"
    MIROC6 = "MIROC6"
    EC_EARTH3_VEG = "EC-Earth3-Veg"
    EC_EARTH3 = "EC-Earth3"
    MPI_ESM1_2_HR = "MPI-ESM1-2-HR"
    MPI_ESM1_2_LR = "MPI-ESM1-2-LR"


class RCMType(str, Enum):
    """Modèles climatiques régionaux (RCM)"""
    CNRM_ALADIN64E1 = "CNRM-ALADIN64E1"
    HCLIM43_ALADIN = "HCLIM43-ALADIN"
    ICON_CLM = "ICON-CLM-202407-1-1"
    RACMO23E = "RACMO23E"
    CNRM_AROME46T1 = "CNRM-AROME46t1"
    CNRM_ALADIN63_EMUL = "CNRM-ALADIN63-emul-CNRM-UNET11-tP22"


class ReferenceDataset(str, Enum):
    """Jeux de données de référence pour l'ajustement statistique"""
    ANASTASIA = "ANASTASIA"
    SAFRAN = "SAFRAN"
    COMEPHORE = "COMEPHORE"


class ClimateDataset(BaseModel):
    """Description d'un jeu de données climatiques"""
    experiment: List[ExperimentType]
    gcm: GCMType
    member: str  # Ex: "r1", "r14", "r15", "r1 à r10"
    downscaling_method: DownscalingMethod
    rcm: RCMType
    reference_dataset: ReferenceDataset
    variables: List[VariableType]
    frequency: Literal["jour", "heure"]
    grid: str  # Ex: "SAFRAN 8km", "ALPX3 2,5km"
    resolution: str  # Ex: "8km", "2.5km"
    period_start: int  # Ex: 1950, 1990, 1850
    period_end: int  # Ex: 2100
    scenario_runs: int  # Nombre de scénarios disponibles


class DatasetMetadata(BaseModel):
    """Métadonnées complètes d'un jeu de données"""
    dataset_id: str
    dataset: ClimateDataset
    file_path: Optional[str] = None  # Chemin vers le fichier NetCDF
    data_url: Optional[str] = None  # URL vers les données sur data.gouv.fr
    available: bool = False  # Si les données sont disponibles localement


class VariableInfo(BaseModel):
    """Informations sur une variable climatique"""
    code: VariableType
    name: str
    unit: str
    description: str


# Informations sur les variables disponibles
VARIABLES_INFO = {
    VariableType.TAS: VariableInfo(
        code=VariableType.TAS,
        name="Température moyenne à 2 mètres",
        unit="K",
        description="Température moyenne de l'atmosphère à 2 mètres"
    ),
    VariableType.TASMIN: VariableInfo(
        code=VariableType.TASMIN,
        name="Température minimale à 2 mètres",
        unit="K",
        description="Température minimale de l'atmosphère à 2 mètres"
    ),
    VariableType.TASMAX: VariableInfo(
        code=VariableType.TASMAX,
        name="Température maximale à 2 mètres",
        unit="K",
        description="Température maximale de l'atmosphère à 2 mètres"
    ),
    VariableType.PR: VariableInfo(
        code=VariableType.PR,
        name="Précipitations",
        unit="kg/m²/s",
        description="Précipitation moyenne (inclut pluie et neige)"
    ),
    VariableType.RSDS: VariableInfo(
        code=VariableType.RSDS,
        name="Rayonnement solaire incident",
        unit="W/m²",
        description="Rayonnement solaire incident (descendant) en surface"
    ),
    VariableType.RLDS: VariableInfo(
        code=VariableType.RLDS,
        name="Rayonnement infrarouge incident",
        unit="W/m²",
        description="Rayonnement infrarouge incident (descendant) en surface"
    ),
    VariableType.HUSS: VariableInfo(
        code=VariableType.HUSS,
        name="Humidité spécifique",
        unit="kg/kg",
        description="Humidité spécifique moyenne de l'atmosphère à 2 mètres"
    ),
    VariableType.SFCWIND: VariableInfo(
        code=VariableType.SFCWIND,
        name="Vitesse du vent",
        unit="m/s",
        description="Vitesse du vent moyen à 10 mètres"
    ),
}


