"""
Définition des jeux de données climatiques disponibles
Basé sur le CSV du hackathon "Le climat en données" 2025
"""

from models import (
    ClimateDataset, ExperimentType, DownscalingMethod, VariableType,
    GCMType, RCMType, ReferenceDataset
)

# Liste des jeux de données disponibles selon le CSV fourni
AVAILABLE_DATASETS = [
    # CNRM-ALADIN64E1 / CNRM-ESM2-1 - r1
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370, ExperimentType.SSP585],
        gcm=GCMType.CNRM_ESM2_1,
        member="r1",
        downscaling_method=DownscalingMethod.RCM,
        rcm=RCMType.CNRM_ALADIN64E1,
        reference_dataset=ReferenceDataset.ANASTASIA,
        variables=[VariableType.TAS, VariableType.TASMIN, VariableType.TASMAX],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1950,
        period_end=2100,
        scenario_runs=2
    ),
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370, ExperimentType.SSP585],
        gcm=GCMType.CNRM_ESM2_1,
        member="r1",
        downscaling_method=DownscalingMethod.RCM,
        rcm=RCMType.CNRM_ALADIN64E1,
        reference_dataset=ReferenceDataset.SAFRAN,
        variables=[VariableType.HUSS, VariableType.PR, VariableType.RLDS, VariableType.RSDS, VariableType.SFCWIND],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1950,
        period_end=2100,
        scenario_runs=0  # Pas de scénarios séparés, mêmes que les températures
    ),
    
    # CNRM-ALADIN64E1 / CNRM-ESM2-1 - r14, r15
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370],
        gcm=GCMType.CNRM_ESM2_1,
        member="r14, r15",
        downscaling_method=DownscalingMethod.RCM,
        rcm=RCMType.CNRM_ALADIN64E1,
        reference_dataset=ReferenceDataset.ANASTASIA,
        variables=[VariableType.TAS, VariableType.TASMIN, VariableType.TASMAX],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1950,
        period_end=2100,
        scenario_runs=2
    ),
    
    # CNRM-ALADIN64E1 / NorESM2-MM
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370, ExperimentType.SSP585],
        gcm=GCMType.NORESM2_MM,
        member="r1",
        downscaling_method=DownscalingMethod.RCM,
        rcm=RCMType.CNRM_ALADIN64E1,
        reference_dataset=ReferenceDataset.ANASTASIA,
        variables=[VariableType.TAS, VariableType.TASMIN, VariableType.TASMAX],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1950,
        period_end=2100,
        scenario_runs=2
    ),
    
    # HCLIM43-ALADIN / IPSL-CM6A-LR
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370],
        gcm=GCMType.IPSL_CM6A_LR,
        member="r1",
        downscaling_method=DownscalingMethod.RCM,
        rcm=RCMType.HCLIM43_ALADIN,
        reference_dataset=ReferenceDataset.ANASTASIA,
        variables=[VariableType.TAS, VariableType.TASMIN, VariableType.TASMAX],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1950,
        period_end=2100,
        scenario_runs=1
    ),
    
    # CNRM-AROME46t1 / CNRM-ESM2-1 (CPRCM haute résolution)
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370],
        gcm=GCMType.CNRM_ESM2_1,
        member="r1",
        downscaling_method=DownscalingMethod.CPRCM,
        rcm=RCMType.CNRM_AROME46T1,
        reference_dataset=ReferenceDataset.ANASTASIA,
        variables=[VariableType.TAS, VariableType.TASMIN, VariableType.TASMAX],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1990,
        period_end=2100,
        scenario_runs=1
    ),
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP370],
        gcm=GCMType.CNRM_ESM2_1,
        member="r1",
        downscaling_method=DownscalingMethod.CPRCM,
        rcm=RCMType.CNRM_AROME46T1,
        reference_dataset=ReferenceDataset.COMEPHORE,
        variables=[VariableType.PR],
        frequency="heure",
        grid="ALPX3 2,5km",
        resolution="2.5km",
        period_start=1990,
        period_end=2100,
        scenario_runs=1
    ),
    
    # EMULATEUR / MPI-ESM1-2-LR (10 membres)
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP126, ExperimentType.SSP245, 
                   ExperimentType.SSP370, ExperimentType.SSP585],
        gcm=GCMType.MPI_ESM1_2_LR,
        member="r1 à r10",
        downscaling_method=DownscalingMethod.EMULATEUR,
        rcm=RCMType.CNRM_ALADIN63_EMUL,
        reference_dataset=ReferenceDataset.ANASTASIA,
        variables=[VariableType.TAS],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1850,
        period_end=2100,
        scenario_runs=40
    ),
    ClimateDataset(
        experiment=[ExperimentType.HISTORICAL, ExperimentType.SSP126, ExperimentType.SSP245,
                   ExperimentType.SSP370, ExperimentType.SSP585],
        gcm=GCMType.MPI_ESM1_2_LR,
        member="r1 à r10",
        downscaling_method=DownscalingMethod.EMULATEUR,
        rcm=RCMType.CNRM_ALADIN63_EMUL,
        reference_dataset=ReferenceDataset.SAFRAN,
        variables=[VariableType.PR],
        frequency="jour",
        grid="SAFRAN 8km",
        resolution="8km",
        period_start=1850,
        period_end=2100,
        scenario_runs=40
    ),
]


def get_datasets_for_variables(variables: list[VariableType]) -> list[ClimateDataset]:
    """Retourne les jeux de données contenant les variables demandées"""
    return [ds for ds in AVAILABLE_DATASETS if any(v in ds.variables for v in variables)]


def get_datasets_for_experiment(experiment: ExperimentType) -> list[ClimateDataset]:
    """Retourne les jeux de données pour un scénario donné"""
    return [ds for ds in AVAILABLE_DATASETS if experiment in ds.experiment]


def get_datasets_for_period(start_year: int, end_year: int) -> list[ClimateDataset]:
    """Retourne les jeux de données couvrant la période demandée"""
    return [ds for ds in AVAILABLE_DATASETS 
            if ds.period_start <= start_year and ds.period_end >= end_year]

