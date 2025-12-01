#!/usr/bin/env python3
"""
Script de debug pour comprendre la structure des données NetCDF
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import xarray as xr
    import numpy as np
except ImportError:
    print("❌ xarray ou numpy non installé")
    sys.exit(1)

def inspect_file(file_path):
    """Inspecte un fichier NetCDF"""
    print(f"\n{'='*80}")
    print(f"📁 Fichier: {file_path.name}")
    print('='*80)
    
    try:
        ds = xr.open_dataset(file_path)
        
        print("\n📊 Variables:")
        for var_name in ds.data_vars:
            var = ds[var_name]
            print(f"  - {var_name}: {var.dims} {var.shape}")
        
        print("\n📍 Coordonnées:")
        for coord_name in ds.coords:
            coord = ds.coords[coord_name]
            print(f"  - {coord_name}: shape={coord.shape}, dtype={coord.dtype}")
            
            if coord_name == 'time':
                time_vals = coord.values
                print(f"    Première date: {time_vals[0]}")
                print(f"    Dernière date: {time_vals[-1]}")
                print(f"    Nombre de pas: {len(time_vals)}")
                print(f"    Type: {type(time_vals[0])}")
                
                # Tester différentes sélections
                print("\n🔍 Tests de sélection temporelle:")
                
                # Test 1: Sélection par année
                try:
                    test_2020 = ds.sel(time='2020')
                    print(f"  ✅ ds.sel(time='2020'): OK, shape={test_2020.dims}")
                except Exception as e:
                    print(f"  ❌ ds.sel(time='2020'): {e}")
                
                # Test 2: Sélection par slice avec dates
                try:
                    test_slice = ds.sel(time=slice('2020-04-15', '2020-06-28'))
                    print(f"  ✅ ds.sel(time=slice('2020-04-15', '2020-06-28')): OK")
                    print(f"     Nombre de pas: {len(test_slice.time)}")
                except Exception as e:
                    print(f"  ❌ ds.sel(time=slice('2020-04-15', '2020-06-28')): {e}")
                
                # Test 3: Vérifier si 2020 existe
                try:
                    # Convertir en pandas DatetimeIndex pour faciliter la recherche
                    import pandas as pd
                    time_index = pd.to_datetime(time_vals)
                    years_available = time_index.year.unique()
                    print(f"  📅 Années disponibles: {sorted(years_available)[:10]}...{sorted(years_available)[-10:]}")
                    
                    if 2020 in years_available:
                        print(f"  ✅ L'année 2020 existe dans les données")
                        dates_2020 = time_index[time_index.year == 2020]
                        print(f"     Dates en 2020: {dates_2020[0]} à {dates_2020[-1]}")
                    else:
                        print(f"  ❌ L'année 2020 n'existe PAS dans les données")
                        closest_year = min(years_available, key=lambda x: abs(x - 2020))
                        print(f"     Année la plus proche: {closest_year}")
                except Exception as e:
                    print(f"  ⚠️  Erreur lors de l'analyse des années: {e}")
            
            elif coord_name in ['lat', 'lon']:
                coord_vals = coord.values
                print(f"    Min: {float(np.min(coord_vals)):.4f}")
                print(f"    Max: {float(np.max(coord_vals)):.4f}")
                print(f"    Nombre de points: {len(coord_vals)}")
        
        # Tester l'extraction d'une variable
        print("\n🔍 Test d'extraction de variable:")
        if len(ds.data_vars) > 0:
            var_name = list(ds.data_vars.keys())[0]
            var_data = ds[var_name]
            print(f"  Variable: {var_name}")
            print(f"  Shape complète: {var_data.shape}")
            
            # Tester une sélection temporelle
            if 'time' in var_data.coords:
                try:
                    # Sélectionner une période qui existe vraiment
                    time_coord = var_data.coords['time']
                    first_time = time_coord.values[0]
                    last_time = time_coord.values[-1]
                    
                    # Utiliser les premières dates disponibles
                    import pandas as pd
                    time_index = pd.to_datetime(time_coord.values)
                    test_start = time_index[0]
                    test_end = time_index[min(100, len(time_index)-1)]  # Prendre les 100 premiers jours
                    
                    test_data = var_data.sel(time=slice(test_start, test_end))
                    print(f"  ✅ Sélection temporelle réussie")
                    print(f"     Période: {test_start} à {test_end}")
                    print(f"     Shape résultante: {test_data.shape}")
                    
                    # Tester une sélection spatiale
                    if 'lat' in var_data.coords and 'lon' in var_data.coords:
                        lat_mid = float(var_data.coords['lat'].values[len(var_data.coords['lat']) // 2])
                        lon_mid = float(var_data.coords['lon'].values[len(var_data.coords['lon']) // 2])
                        
                        test_point = test_data.sel(lat=lat_mid, lon=lon_mid, method='nearest')
                        print(f"  ✅ Sélection spatiale réussie pour ({lat_mid:.2f}, {lon_mid:.2f})")
                        print(f"     Shape: {test_point.shape}")
                        print(f"     Valeurs (premiers 5): {test_point.values[:5] if len(test_point.values) > 0 else 'N/A'}")
                        
                except Exception as e:
                    print(f"  ❌ Erreur lors de l'extraction: {e}")
                    import traceback
                    traceback.print_exc()
        
        ds.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Chercher les fichiers .nc
    possible_paths = [
        Path(__file__).parent / "data",
        Path(__file__).parent.parent / "data",
    ]
    
    nc_files = []
    for path in possible_paths:
        if path.exists():
            nc_files.extend(list(path.glob("*.nc")))
    
    if not nc_files:
        print("❌ Aucun fichier .nc trouvé")
        sys.exit(1)
    
    print(f"📁 {len(nc_files)} fichier(s) trouvé(s)\n")
    
    for nc_file in nc_files:
        inspect_file(nc_file)


