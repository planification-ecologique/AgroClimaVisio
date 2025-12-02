"""
Module pour charger et interroger les données climatiques via DuckDB
Optimisé pour accès rapide point par point (carré de grille)
"""

try:
    import duckdb
    import xarray as xr
    import numpy as np
    import pandas as pd
    import netCDF4 as nc
    from pathlib import Path
    from typing import Optional, Dict, List, Tuple
    from datetime import date, datetime
    DUCKDB_AVAILABLE = True
    NETCDF4_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    NETCDF4_AVAILABLE = False
    duckdb = None
    xr = None
    np = None
    pd = None
    nc = None

import logging
from models import VariableType, ExperimentType

logger = logging.getLogger(__name__)


class DuckDBClimateLoader:
    """
    Chargeur de données climatiques utilisant DuckDB pour accès rapide.
    Optimisé pour requêtes point par point (carré de grille).
    """
    
    def __init__(self, db_path: Optional[str] = None, data_directory: Optional[str] = None):
        """
        Initialise le chargeur DuckDB.
        
        Args:
            db_path: Chemin vers le fichier DuckDB (créé si n'existe pas)
            data_directory: Répertoire contenant les fichiers NetCDF sources
        """
        if not DUCKDB_AVAILABLE:
            raise ImportError(
                "DuckDB n'est pas installé. Installez-le avec: "
                "poetry add duckdb"
            )
        
        self.db_path = Path(db_path) if db_path else Path("climate_data.duckdb")
        self.data_directory = Path(data_directory) if data_directory else None
        
        # Connexion DuckDB avec gestion d'erreurs pour les verrous
        try:
            self.conn = duckdb.connect(str(self.db_path))
        except Exception as e:
            if "lock" in str(e).lower() or "conflicting" in str(e).lower():
                raise IOError(
                    f"Le fichier DuckDB est verrouillé par un autre processus.\n"
                    f"Vérifiez qu'aucune autre instance du script ne tourne.\n"
                    f"Vous pouvez tuer le processus avec: kill <PID>\n"
                    f"Erreur originale: {e}"
                )
            raise
        
        # Créer le schéma si nécessaire
        self._create_schema()
    
    def _create_schema(self):
        """Crée le schéma de la base de données si nécessaire"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS climate_data (
                variable VARCHAR NOT NULL,
                experiment VARCHAR NOT NULL,
                gcm VARCHAR NOT NULL,
                rcm VARCHAR NOT NULL,
                member VARCHAR NOT NULL,
                lat DOUBLE NOT NULL,
                lon DOUBLE NOT NULL,
                time DATE NOT NULL,
                value DOUBLE NOT NULL
            );
        """)
        
        # Créer les index pour performance
        try:
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_spatial ON climate_data(lat, lon);")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_temporal ON climate_data(time);")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_variable ON climate_data(variable, experiment, gcm, rcm);")
        except Exception as e:
            # Les index peuvent déjà exister
            logger.debug(f"Index creation: {e}")
    
    def import_netcdf_file(
        self,
        file_path: str,
        variable: VariableType,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        member: str = "r1",
        chunk_size: int = 5000  # Réduit pour économiser la mémoire
    ) -> int:
        """
        Importe un fichier NetCDF dans DuckDB de manière optimisée en mémoire.
        Traite les données par chunks temporels pour éviter de charger tout en mémoire.
        
        Args:
            file_path: Chemin vers le fichier NetCDF
            variable: Variable climatique
            experiment: Scénario climatique
            gcm: Modèle climatique global
            rcm: Modèle climatique régional
            member: Membre d'ensemble
            chunk_size: Nombre de lignes à insérer par batch dans DuckDB
            time_chunk_size: Nombre de pas de temps à traiter à la fois
        
        Returns:
            Nombre de lignes importées
        """
        if not DUCKDB_AVAILABLE or not xr:
            raise ImportError("xarray et duckdb doivent être installés")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
        
        logger.info(f"Importation de {file_path} dans DuckDB (mode optimisé mémoire)...")
        print(f"   📂 Ouverture du fichier NetCDF avec netCDF4 (accès direct aux slices)...")
        
        # Utiliser netCDF4 directement pour un accès plus efficace aux slices
        # Cela évite l'overhead de xarray et permet un accès direct optimisé
        if NETCDF4_AVAILABLE:
            nc_file = nc.Dataset(file_path, 'r')
            print(f"   ✅ Fichier ouvert avec netCDF4")
        else:
            # Fallback sur xarray si netCDF4 n'est pas disponible
            ds = xr.open_dataset(file_path)
            print(f"   ✅ Fichier ouvert avec xarray")
            nc_file = None
        
        # Trouver la variable dans le dataset
        var_names = {
            VariableType.PR: ["prAdjust", "prAdjusted", "pr"],
            VariableType.TAS: ["tasAdjust", "tasAdjusted", "tas"],
            VariableType.TASMAX: ["tasmaxAdjust", "tasmaxAdjusted", "tasmax"],
            VariableType.TASMIN: ["tasminAdjust", "tasminAdjusted", "tasmin"],
            VariableType.RSDS: ["rsdsAdjust", "rsdsAdjusted", "rsds"],
            VariableType.RLDS: ["rldsAdjust", "rldsAdjusted", "rlds"],
            VariableType.HUSS: ["hussAdjust", "hussAdjusted", "huss"],
            VariableType.SFCWIND: ["sfcWindAdjust", "sfcWindAdjusted", "sfcWind"]
        }
        
        var_name = None
        if nc_file:
            # Utiliser netCDF4 directement
            for name in var_names.get(variable, [variable.value]):
                if name in nc_file.variables:
                    var_name = name
                    break
            
            if not var_name:
                nc_file.close()
                raise ValueError(f"Variable {variable.value} non trouvée dans {file_path}")
            
            print(f"   🔍 Variable trouvée: {var_name}")
            nc_var = nc_file.variables[var_name]
            nc_time = nc_file.variables['time']
            nc_lat = nc_file.variables['lat']
            nc_lon = nc_file.variables['lon']
            
            # Obtenir les dimensions directement depuis netCDF4
            print(f"   📊 Lecture des dimensions...")
            time_coords = nc_time[:]
            lat_coords_raw = nc_lat[:]
            lon_coords_raw = nc_lon[:]
            
            # Obtenir la shape de la variable
            var_shape = nc_var.shape
            print(f"   📐 Shape de la variable: {var_shape}")
        else:
            # Fallback sur xarray
            for name in var_names.get(variable, [variable.value]):
                if name in ds.data_vars:
                    var_name = name
                    break
            
            if not var_name:
                raise ValueError(f"Variable {variable.value} non trouvée dans {file_path}")
            
            print(f"   🔍 Variable trouvée: {var_name}")
            data_array = ds[var_name]
            
            if 'lat' not in data_array.coords or 'lon' not in data_array.coords:
                raise ValueError("Coordonnées 'lat' et 'lon' non trouvées dans le dataset")
            
            print(f"   📊 Lecture des dimensions...")
            time_coords = data_array.coords['time'].values
            lat_coords_raw = data_array.coords['lat'].values
            lon_coords_raw = data_array.coords['lon'].values
            var_shape = data_array.shape
            nc_var = None
        
        # Vérifier si les coordonnées sont 1D ou 2D
        lat_shape = lat_coords_raw.shape if hasattr(lat_coords_raw, 'shape') else None
        lon_shape = lon_coords_raw.shape if hasattr(lon_coords_raw, 'shape') else None
        
        logger.info(f"Forme des coordonnées lat: {lat_shape}, lon: {lon_shape}")
        print(f"   📐 Forme des coordonnées lat: {lat_shape}, lon: {lon_shape}")
        
        # Obtenir les dimensions de la grille
        # Si les coordonnées sont 2D, utiliser les dimensions de la grille
        # Sinon, utiliser les dimensions des coordonnées 1D
        if lat_shape and len(lat_shape) == 2:
            # Grille 2D: les coordonnées sont des arrays 2D
            n_lats, n_lons = lat_shape
            logger.info(f"Grille 2D détectée: {n_lats} × {n_lons}")
        else:
            # Coordonnées 1D: dimensions séparées
            n_lats = len(lat_coords_raw) if hasattr(lat_coords_raw, '__len__') else 1
            n_lons = len(lon_coords_raw) if hasattr(lon_coords_raw, '__len__') else 1
            logger.info(f"Coordonnées 1D détectées: {n_lats} lat × {n_lons} lon")
        
        n_times = len(time_coords)
        
        def to_float(val):
            """Convertit une valeur en float Python"""
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, (np.integer, np.floating)):
                return float(val)
            if hasattr(val, 'shape') and val.shape == ():
                return float(val.item())
            if hasattr(val, '__len__') and len(val) == 1:
                return float(val[0])
            return float(val)
        
        logger.info(f"Dimensions: {n_times} temps × {n_lats} lat × {n_lons} lon = {n_times * n_lats * n_lons:,} points")
        print(f"   📏 Dimensions: {n_times} temps × {n_lats} lat × {n_lons} lon = {n_times * n_lats * n_lons:,} points")
        
        # Pré-calculer les coordonnées si grille 2D (une seule fois au début)
        lat_coords_2d = None
        lon_coords_2d = None
        if lat_shape and len(lat_shape) == 2:
            print(f"   🔄 Pré-calcul des coordonnées 2D ({n_lats} × {n_lons} = {n_lats * n_lons:,} points)...")
            # Convertir toutes les coordonnées une seule fois pour éviter les conversions répétées
            lat_coords_2d = np.array([[to_float(lat_coords_raw[i, j]) for j in range(n_lons)] for i in range(n_lats)])
            lon_coords_2d = np.array([[to_float(lon_coords_raw[i, j]) for j in range(n_lons)] for i in range(n_lats)])
            print(f"   ✅ Coordonnées pré-calculées")
        
        print(f"   🚀 Début de l'importation...")
        
        total_rows = 0
        rows_buffer = []
        
        # Traiter pas de temps par pas de temps pour minimiser la mémoire
        for t_idx, time_val in enumerate(time_coords):
            if t_idx % 100 == 0 or t_idx == 0:
                logger.info(f"Traitement du pas de temps {t_idx+1}/{n_times}...")
                print(f"   ⏳ Traitement du pas de temps {t_idx+1}/{n_times}...")
            
            # Charger seulement UN pas de temps à la fois
            # Utiliser netCDF4 pour un accès direct optimisé au slice
            time_slice = None
            if nc_var is not None:
                # Accès direct avec netCDF4 - beaucoup plus rapide que xarray
                # Lire directement le slice [t_idx, :, :] sans overhead
                # Selon https://annefou.github.io/metos_python/07-LargeFiles/, 
                # netCDF4 permet un accès direct aux slices sans charger tout le fichier
                values_2d = nc_var[t_idx, :, :]  # Shape: (lat, lon)
                # Gérer les valeurs masquées (masked arrays) en les convertissant en NaN
                if hasattr(values_2d, 'mask'):
                    # Si c'est un masked array, convertir en array numpy normal avec NaN
                    values_2d = np.ma.filled(values_2d, np.nan)
            else:
                # Fallback sur xarray
                time_slice = data_array.isel(time=t_idx)
                values_2d = time_slice.load().values  # Shape: (lat, lon) ou (y, x)
            
            # Convertir la date une seule fois
            if hasattr(time_val, 'date'):
                time_date = time_val.date()
            elif hasattr(time_val, 'item'):
                time_date = pd.to_datetime(time_val.item()).date()
            else:
                time_date = pd.to_datetime(time_val).date()
            
            # Itérer sur les indices de la grille
            for lat_idx in range(n_lats):
                for lon_idx in range(n_lons):
                    value = float(values_2d[lat_idx, lon_idx])
                    
                    # Ignorer les NaN
                    if np.isnan(value):
                        continue
                    
                    # Extraire les coordonnées lat/lon pour ce point de grille
                    if lat_coords_2d is not None:
                        # Grille 2D: utiliser les coordonnées pré-calculées
                        lat_val = float(lat_coords_2d[lat_idx, lon_idx])
                        lon_val = float(lon_coords_2d[lat_idx, lon_idx])
                    else:
                        # Coordonnées 1D: utiliser les indices directement
                        lat_val = to_float(lat_coords_raw[lat_idx])
                        lon_val = to_float(lon_coords_raw[lon_idx])
                    
                    rows_buffer.append({
                        'variable': variable.value,
                        'experiment': experiment.value,
                        'gcm': gcm,
                        'rcm': rcm,
                        'member': member,
                        'lat': lat_val,
                        'lon': lon_val,
                        'time': time_date,
                        'value': value
                    })
                    
                    # Insérer par batch pour éviter d'accumuler trop en mémoire
                    if len(rows_buffer) >= chunk_size:
                        df_chunk = pd.DataFrame(rows_buffer)
                        # Enregistrer le DataFrame comme table temporaire
                        self.conn.register('temp_chunk', df_chunk)
                        # Insérer depuis la table temporaire
                        self.conn.execute("INSERT INTO climate_data SELECT * FROM temp_chunk")
                        # Nettoyer la table temporaire
                        self.conn.unregister('temp_chunk')
                        total_rows += len(rows_buffer)
                        rows_buffer = []
                        
                        # Afficher progression
                        if total_rows % (chunk_size * 10) == 0:
                            logger.info(f"  Progression: {total_rows:,} lignes importées...")
                            print(f"   💾 {total_rows:,} lignes importées dans la base...")
            
            # Libérer la mémoire après chaque pas de temps
            if time_slice is not None:
                del time_slice
            del values_2d
        
        # Insérer les dernières lignes
        if rows_buffer:
            df_chunk = pd.DataFrame(rows_buffer)
            self.conn.register('temp_chunk', df_chunk)
            self.conn.execute("INSERT INTO climate_data SELECT * FROM temp_chunk")
            self.conn.unregister('temp_chunk')
            total_rows += len(rows_buffer)
        
            logger.info(f"✅ Importation terminée: {total_rows:,} lignes")
            print(f"   ✅ Importation terminée: {total_rows:,} lignes")
        
        # Fermer proprement les fichiers
        if nc_file:
            nc_file.close()
        elif 'ds' in locals():
            ds.close()
        
        return total_rows
    
    def get_data_for_grid_cell(
        self,
        lat: float,
        lon: float,
        variables: List[VariableType],
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        member: str = "r1",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        tolerance: float = 0.05  # Tolérance en degrés pour trouver le point le plus proche
    ) -> pd.DataFrame:
        """
        Récupère toutes les données pour un carré de grille donné.
        
        Args:
            lat: Latitude du point
            lon: Longitude du point
            variables: Liste des variables à récupérer
            experiment: Scénario climatique
            gcm: Modèle climatique global
            rcm: Modèle climatique régional
            member: Membre d'ensemble
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            tolerance: Tolérance en degrés pour trouver le point le plus proche
        
        Returns:
            DataFrame avec colonnes: variable, time, value
        """
        var_names = [v.value for v in variables]
        
        query = """
            SELECT 
                variable,
                time,
                value,
                lat,
                lon
            FROM climate_data
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
              AND variable IN ({})
              AND experiment = ?
              AND gcm = ?
              AND rcm = ?
              AND member = ?
        """.format(','.join(['?' for _ in var_names]))
        
        params = [
            lat - tolerance,
            lat + tolerance,
            lon - tolerance,
            lon + tolerance
        ] + var_names + [
            experiment.value,
            gcm,
            rcm,
            member
        ]
        
        if start_date:
            query += " AND time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND time <= ?"
            params.append(end_date)
        
        query += " ORDER BY variable, time"
        
        result = self.conn.execute(query, params).df()
        
        # Si plusieurs points dans la tolérance, prendre le plus proche
        if len(result) > 0 and len(result.groupby(['variable', 'time'])) > len(result) / len(var_names):
            # Il y a plusieurs points spatiaux, prendre le plus proche
            result['distance'] = np.sqrt(
                (result['lat'] - lat)**2 + (result['lon'] - lon)**2
            )
            result = result.sort_values('distance').groupby(['variable', 'time']).first().reset_index()
            result = result.drop(columns=['distance', 'lat', 'lon'])
        
        return result
    
    def get_aggregated_data(
        self,
        lat: float,
        lon: float,
        variable: VariableType,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        member: str = "r1",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        aggregation: str = "mean"  # 'mean', 'sum', 'min', 'max', 'count'
    ) -> float:
        """
        Récupère une valeur agrégée pour un point et une période.
        
        Args:
            lat: Latitude
            lon: Longitude
            variable: Variable climatique
            experiment: Scénario climatique
            gcm: Modèle climatique global
            rcm: Modèle climatique régional
            member: Membre d'ensemble
            start_date: Date de début
            end_date: Date de fin
            aggregation: Type d'agrégation ('mean', 'sum', 'min', 'max', 'count')
        
        Returns:
            Valeur agrégée
        """
        agg_func = {
            'mean': 'AVG',
            'sum': 'SUM',
            'min': 'MIN',
            'max': 'MAX',
            'count': 'COUNT'
        }.get(aggregation.lower(), 'AVG')
        
        query = f"""
            SELECT {agg_func}(value) as result
            FROM climate_data
            WHERE ABS(lat - ?) < 0.05
              AND ABS(lon - ?) < 0.05
              AND variable = ?
              AND experiment = ?
              AND gcm = ?
              AND rcm = ?
              AND member = ?
        """
        
        params = [lat, lon, variable.value, experiment.value, gcm, rcm, member]
        
        if start_date:
            query += " AND time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND time <= ?"
            params.append(end_date)
        
        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else None
    
    def get_time_series(
        self,
        lat: float,
        lon: float,
        variable: VariableType,
        experiment: ExperimentType,
        gcm: str,
        rcm: str,
        member: str = "r1",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Récupère une série temporelle pour un point et une variable.
        
        Returns:
            DataFrame avec colonnes: time, value
        """
        query = """
            SELECT time, value
            FROM climate_data
            WHERE ABS(lat - ?) < 0.05
              AND ABS(lon - ?) < 0.05
              AND variable = ?
              AND experiment = ?
              AND gcm = ?
              AND rcm = ?
              AND member = ?
        """
        
        params = [lat, lon, variable.value, experiment.value, gcm, rcm, member]
        
        if start_date:
            query += " AND time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND time <= ?"
            params.append(end_date)
        
        query += " ORDER BY time"
        
        return self.conn.execute(query, params).df()
    
    def close(self):
        """Ferme la connexion DuckDB"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

