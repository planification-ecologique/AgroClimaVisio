#!/usr/bin/env python3
"""
Exemple d'utilisation de DuckDB pour accès rapide aux données par carré de grille
Usage: poetry run python example_duckdb_usage.py
       ou: poetry shell puis python example_duckdb_usage.py
"""

from pathlib import Path
from datetime import date
from duckdb_loader import DuckDBClimateLoader
from models import VariableType, ExperimentType

def main():
    # Chemin vers la base DuckDB
    db_path = Path(__file__).parent / "climate_data.duckdb"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        print("   Exécutez d'abord: python import_to_duckdb.py")
        return
    
    # Créer le chargeur
    loader = DuckDBClimateLoader(db_path=str(db_path))
    
    # Exemple 1: Récupérer toutes les données pour un carré de grille
    print("=" * 80)
    print("Exemple 1: Données pour un carré de grille (Toulouse)")
    print("=" * 80)
    
    lat_toulouse = 43.6047
    lon_toulouse = 1.4437
    
    df = loader.get_data_for_grid_cell(
        lat=lat_toulouse,
        lon=lon_toulouse,
        variables=[VariableType.PR, VariableType.TAS],  # Si vous avez ces variables
        experiment=ExperimentType.SSP370,
        gcm="CNRM-ESM2-1",
        rcm="CNRM-ALADIN64E1",
        member="r1",
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31)
    )
    
    print(f"\n📊 {len(df)} lignes récupérées")
    print(df.head(20))
    
    # Exemple 2: Série temporelle pour une variable
    print("\n" + "=" * 80)
    print("Exemple 2: Série temporelle de précipitations")
    print("=" * 80)
    
    ts = loader.get_time_series(
        lat=lat_toulouse,
        lon=lon_toulouse,
        variable=VariableType.PR,
        experiment=ExperimentType.SSP370,
        gcm="CNRM-ESM2-1",
        rcm="CNRM-ALADIN64E1",
        member="r1",
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31)
    )
    
    print(f"\n📈 {len(ts)} jours de données")
    print(ts.head(10))
    print(f"\n📊 Statistiques:")
    print(ts.describe())
    
    # Exemple 3: Agrégation (cumul annuel)
    print("\n" + "=" * 80)
    print("Exemple 3: Cumul annuel de précipitations")
    print("=" * 80)
    
    total_pr = loader.get_aggregated_data(
        lat=lat_toulouse,
        lon=lon_toulouse,
        variable=VariableType.PR,
        experiment=ExperimentType.SSP370,
        gcm="CNRM-ESM2-1",
        rcm="CNRM-ALADIN64E1",
        member="r1",
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
        aggregation="sum"
    )
    
    print(f"\n💧 Cumul annuel 2020: {total_pr:.2f} mm")
    
    # Exemple 4: Requête SQL personnalisée
    print("\n" + "=" * 80)
    print("Exemple 4: Requête SQL personnalisée (moyennes mensuelles)")
    print("=" * 80)
    
    monthly = loader.conn.execute("""
        SELECT 
            EXTRACT(YEAR FROM time) as year,
            EXTRACT(MONTH FROM time) as month,
            AVG(value) as avg_value,
            SUM(value) as total_value
        FROM climate_data
        WHERE ABS(lat - ?) < 0.05
          AND ABS(lon - ?) < 0.05
          AND variable = ?
          AND experiment = ?
          AND gcm = ?
          AND rcm = ?
          AND member = ?
          AND time >= ?
          AND time <= ?
        GROUP BY year, month
        ORDER BY year, month
    """, [
        lat_toulouse,
        lon_toulouse,
        VariableType.PR.value,
        ExperimentType.SSP370.value,
        "CNRM-ESM2-1",
        "CNRM-ALADIN64E1",
        "r1",
        date(2020, 1, 1),
        date(2020, 12, 31)
    ]).df()
    
    print(f"\n📅 Moyennes mensuelles:")
    print(monthly.to_string(index=False))
    
    loader.close()
    print("\n✅ Exemples terminés!")

if __name__ == "__main__":
    main()

