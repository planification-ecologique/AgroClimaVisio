#!/usr/bin/env python3
"""
Script pour importer les fichiers NetCDF dans DuckDB
Usage: poetry run python import_to_duckdb.py
       ou: poetry shell puis python import_to_duckdb.py
"""

import sys
import re
from pathlib import Path
from duckdb_loader import DuckDBClimateLoader
from models import VariableType, ExperimentType
from points_config import get_all_points

def main():
    # Configuration
    data_dir = Path(__file__).parent / "data"
    db_path = Path(__file__).parent / "data" / "climate_data.duckdb"
    
    if not data_dir.exists():
        print(f"❌ Répertoire de données non trouvé: {data_dir}")
        sys.exit(1)
    
    # Créer le chargeur DuckDB avec gestion d'erreurs
    try:
        loader = DuckDBClimateLoader(db_path=str(db_path), data_directory=str(data_dir))
    except IOError as e:
        print("❌ Erreur de connexion à la base de données:")
        print(f"   {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Trouver les fichiers NetCDF
    nc_files = list(data_dir.glob("*.nc"))
    
    if not nc_files:
        print(f"❌ Aucun fichier .nc trouvé dans {data_dir}")
        sys.exit(1)
    
    print(f"📁 {len(nc_files)} fichier(s) .nc trouvé(s)\n")
    
    # Mapper les noms de fichiers aux variables et configurations
    def detect_file_config(file_path: Path):
        """Détecte automatiquement la configuration d'un fichier NetCDF"""
        filename = file_path.name
        
        # Détecter la variable depuis le nom de fichier
        variable_map = {
            'prAdjust': VariableType.PR,
            'tasAdjust': VariableType.TAS,
            'tasmaxAdjust': VariableType.TASMAX,
            'tasminAdjust': VariableType.TASMIN,
        }
        
        variable = None
        for var_name, var_type in variable_map.items():
            if var_name in filename:
                variable = var_type
                break
        
        if variable is None:
            return None
        
        # Détecter l'expérience (scénario)
        if 'historical' in filename:
            experiment = ExperimentType.HISTORICAL
        elif 'ssp370' in filename:
            experiment = ExperimentType.SSP370
        elif 'ssp585' in filename:
            experiment = ExperimentType.SSP585
        elif 'ssp245' in filename:
            experiment = ExperimentType.SSP245
        elif 'ssp126' in filename:
            experiment = ExperimentType.SSP126
        else:
            experiment = ExperimentType.SSP370  # Par défaut
        
        # Détecter le GCM depuis le nom de fichier
        # Format: ..._CNRM-ESM2-1_... ou ..._MPI-ESM1-2-LR_...
        if 'MPI-ESM1-2-LR' in filename:
            gcm = "MPI-ESM1-2-LR"
        elif 'CNRM-ESM2-1' in filename:
            gcm = "CNRM-ESM2-1"
        else:
            gcm = "CNRM-ESM2-1"  # Par défaut
        
        # Détecter le RCM depuis le nom de fichier
        rcm = "CNRM-ALADIN64E1"  # Par défaut
        if 'AROME46t1' in filename:
            rcm = "CNRM-AROME46T1"
        elif 'ALADIN64E1' in filename:
            rcm = "CNRM-ALADIN64E1"
        elif 'ALADIN63-emul' in filename or 'ALADIN63_emul' in filename:
            rcm = "CNRM-ALADIN63-EMUL"
        
        # Détecter le membre d'ensemble (r1, r10, etc.)
        # Format: ..._r10i1p1f1_... ou ..._r1i1p1f2_...
        member_match = re.search(r'_r(\d+)i\d+p\d+f\d+_', filename)
        if member_match:
            member = f"r{member_match.group(1)}"
        else:
            member = "r1"  # Par défaut
        
        return {
            "file_path": file_path,
            "variable": variable,
            "experiment": experiment,
            "gcm": gcm,
            "rcm": rcm,
            "member": member
        }
    
    # Détecter automatiquement la configuration de tous les fichiers
    datasets_config = []
    for file_path in sorted(nc_files):
        config = detect_file_config(file_path)
        if config:
            datasets_config.append(config)
            print(f"✅ {file_path.name}")
            print(f"   → Variable: {config['variable'].value}, Experiment: {config['experiment'].value}, RCM: {config['rcm']}")
        else:
            print(f"⚠️  {file_path.name} - Variable non reconnue")
    
    print(f"\n📊 {len(datasets_config)} fichier(s) configuré(s) pour l'import\n")
    
    total_imported = 0
    
    for config in datasets_config:
        file_path = config["file_path"]
        print(f"\n📥 Importation de: {file_path.name}")
        print(f"   Variable: {config['variable'].value}")
        print(f"   Experiment: {config['experiment'].value}")
        print(f"   GCM: {config['gcm']}, RCM: {config['rcm']}")
        
        try:
            # Déterminer la période de filtrage selon le type de fichier
            # Les fichiers tas* vont seulement jusqu'à 2019, donc utiliser toute la période disponible
            if config["variable"] in [VariableType.TAS, VariableType.TASMAX, VariableType.TASMIN]:
                # Pour les températures, utiliser toute la période disponible (2015-2019)
                start_year = None  # Pas de filtre de début
                end_year = None    # Pas de filtre de fin
            else:
                # Pour les précipitations, filtrer 2025-2100
                start_year = 2025
                end_year = 2100
            
            # Points représentatifs de la Beauce et de la Bretagne
            # Utiliser la configuration centralisée
            all_points_lat, all_points_lon = get_all_points(format="lat_lon")
            
            rows = loader.import_netcdf_file(
                file_path=str(file_path),
                variable=config["variable"],
                experiment=config["experiment"],
                gcm=config["gcm"],
                rcm=config["rcm"],
                member=config["member"],
                # Filtrer pour les points représentatifs de la Beauce et de la Bretagne
                lat_filter=all_points_lat,
                lon_filter=all_points_lon,
                start_year=start_year,
                end_year=end_year
            )
            total_imported += rows
            print(f"   ✅ {rows:,} lignes importées")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Importation terminée: {total_imported:,} lignes au total")
    print(f"📊 Base de données: {db_path}")
    
    # Afficher quelques statistiques
    print("\n📈 Statistiques:")
    stats = loader.conn.execute("""
        SELECT 
            variable,
            experiment,
            COUNT(*) as count,
            MIN(time) as min_date,
            MAX(time) as max_date,
            COUNT(DISTINCT lat) as n_lat,
            COUNT(DISTINCT lon) as n_lon
        FROM climate_data
        GROUP BY variable, experiment
        ORDER BY variable, experiment
    """).df()
    
    print(stats.to_string(index=False))
    
    # Fermer proprement la connexion
    try:
        loader.close()
    except Exception as e:
        print(f"⚠️  Erreur lors de la fermeture: {e}")

if __name__ == "__main__":
    main()

