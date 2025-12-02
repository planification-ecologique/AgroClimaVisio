#!/usr/bin/env python3
"""
Script pour importer les fichiers NetCDF dans DuckDB
Usage: poetry run python import_to_duckdb.py
       ou: poetry shell puis python import_to_duckdb.py
"""

import sys
from pathlib import Path
from duckdb_loader import DuckDBClimateLoader
from models import VariableType, ExperimentType

def main():
    # Configuration
    data_dir = Path(__file__).parent / "data"
    db_path = Path(__file__).parent / "climate_data.duckdb"
    
    if not data_dir.exists():
        print(f"❌ Répertoire de données non trouvé: {data_dir}")
        sys.exit(1)
    
    # Créer le chargeur DuckDB avec gestion d'erreurs
    try:
        loader = DuckDBClimateLoader(db_path=str(db_path), data_directory=str(data_dir))
    except IOError as e:
        print(f"❌ Erreur de connexion à la base de données:")
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
    
    # Configuration des datasets (à adapter selon vos fichiers)
    # Exemple basé sur les fichiers actuels
    datasets_config = [
        {
            "file_pattern": "*historical*.nc",
            "variable": VariableType.PR,
            "experiment": ExperimentType.HISTORICAL,
            "gcm": "CNRM-ESM2-1",
            "rcm": "CNRM-ALADIN64E1",
            "member": "r1"
        },
        {
            "file_pattern": "*ssp370*.nc",
            "variable": VariableType.PR,
            "experiment": ExperimentType.SSP370,
            "gcm": "CNRM-ESM2-1",
            "rcm": "CNRM-ALADIN64E1",
            "member": "r1"
        }
    ]
    
    total_imported = 0
    
    for config in datasets_config:
        # Trouver le fichier correspondant
        matching_files = list(data_dir.glob(config["file_pattern"]))
        
        if not matching_files:
            print(f"⚠️  Aucun fichier trouvé pour pattern: {config['file_pattern']}")
            continue
        
        for file_path in matching_files:
            print(f"\n📥 Importation de: {file_path.name}")
            print(f"   Variable: {config['variable'].value}")
            print(f"   Experiment: {config['experiment'].value}")
            
            try:
                rows = loader.import_netcdf_file(
                    file_path=str(file_path),
                    variable=config["variable"],
                    experiment=config["experiment"],
                    gcm=config["gcm"],
                    rcm=config["rcm"],
                    member=config["member"]
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

