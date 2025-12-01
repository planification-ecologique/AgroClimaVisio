#!/usr/bin/env python3
"""
Script pour inspecter la structure des fichiers NetCDF
"""

import sys
from pathlib import Path
import xarray as xr
import numpy as np

def inspect_nc_file(file_path):
    """Inspecte un fichier NetCDF et affiche sa structure"""
    print(f"📁 Inspection de: {file_path}\n")
    
    try:
        ds = xr.open_dataset(file_path)
        
        print("=" * 80)
        print("STRUCTURE DU DATASET")
        print("=" * 80)
        
        print("\n📊 Variables de données:")
        for var_name, var in ds.data_vars.items():
            print(f"  - {var_name}:")
            print(f"      Shape: {var.shape}")
            print(f"      Dtype: {var.dtype}")
            print(f"      Dims: {var.dims}")
            if 'units' in var.attrs:
                print(f"      Units: {var.attrs['units']}")
            if 'long_name' in var.attrs:
                print(f"      Long name: {var.attrs['long_name']}")
        
        print("\n📍 Coordonnées:")
        for coord_name, coord in ds.coords.items():
            print(f"  - {coord_name}:")
            print(f"      Shape: {coord.shape}")
            print(f"      Dtype: {coord.dtype}")
            print(f"      Values (first 5): {coord.values[:5] if len(coord.values) > 0 else coord.values}")
            if len(coord.values) > 5:
                print(f"      Values (last 5): {coord.values[-5:]}")
            if 'units' in coord.attrs:
                print(f"      Units: {coord.attrs['units']}")
        
        print("\n📅 Période temporelle:")
        if 'time' in ds.coords:
            time_coord = ds.coords['time']
            print(f"  - Première date: {time_coord.values[0]}")
            print(f"  - Dernière date: {time_coord.values[-1]}")
            print(f"  - Nombre de pas de temps: {len(time_coord)}")
            print(f"  - Type: {type(time_coord.values[0])}")
        
        print("\n🗺️  Étendue spatiale:")
        if 'lat' in ds.coords:
            lat_coord = ds.coords['lat']
            print(f"  - Latitude min: {float(lat_coord.min().values)}")
            print(f"  - Latitude max: {float(lat_coord.max().values)}")
            print(f"  - Nombre de points: {len(lat_coord)}")
        
        if 'lon' in ds.coords:
            lon_coord = ds.coords['lon']
            print(f"  - Longitude min: {float(lon_coord.min().values)}")
            print(f"  - Longitude max: {float(lon_coord.max().values)}")
            print(f"  - Nombre de points: {len(lon_coord)}")
        
        print("\n📋 Attributs globaux:")
        for attr_name, attr_value in ds.attrs.items():
            if len(str(attr_value)) < 100:
                print(f"  - {attr_name}: {attr_value}")
            else:
                print(f"  - {attr_name}: {str(attr_value)[:100]}...")
        
        print("\n🔍 Test de sélection temporelle:")
        if 'time' in ds.coords:
            # Tester une sélection pour 2020
            try:
                test_2020 = ds.sel(time='2020')
                print(f"  ✅ Sélection '2020' réussie: shape={test_2020.dims}")
            except Exception as e:
                print(f"  ❌ Sélection '2020' échouée: {e}")
            
            # Tester une sélection par slice
            try:
                test_slice = ds.sel(time=slice('2020-04-15', '2020-06-28'))
                print(f"  ✅ Sélection slice réussie: shape={test_slice.dims}")
                if len(test_slice.time) > 0:
                    print(f"     Nombre de pas de temps: {len(test_slice.time)}")
            except Exception as e:
                print(f"  ❌ Sélection slice échouée: {e}")
        
        print("\n🔍 Test d'extraction d'une variable:")
        if len(ds.data_vars) > 0:
            var_name = list(ds.data_vars.keys())[0]
            var_data = ds[var_name]
            print(f"  Variable: {var_name}")
            print(f"  Shape complète: {var_data.shape}")
            
            # Tester une sélection spatiale
            if 'lat' in ds.coords and 'lon' in ds.coords:
                try:
                    lat_mid = float(ds.coords['lat'].values[len(ds.coords['lat']) // 2])
                    lon_mid = float(ds.coords['lon'].values[len(ds.coords['lon']) // 2])
                    test_point = var_data.sel(lat=lat_mid, lon=lon_mid, method='nearest')
                    print(f"  ✅ Sélection spatiale réussie pour ({lat_mid}, {lon_mid})")
                    print(f"     Shape résultante: {test_point.shape}")
                except Exception as e:
                    print(f"  ❌ Sélection spatiale échouée: {e}")
        
        ds.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'inspection: {e}")
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
    
    # Inspecter le premier fichier trouvé
    print(f"📁 {len(nc_files)} fichier(s) .nc trouvé(s)\n")
    inspect_nc_file(nc_files[0])
    
    if len(nc_files) > 1:
        print("\n" + "=" * 80)
        print("DEUXIÈME FICHIER")
        print("=" * 80 + "\n")
        inspect_nc_file(nc_files[1])


