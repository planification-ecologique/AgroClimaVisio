"""
Configuration des points représentatifs pour l'analyse climatique

Ce module définit les points géographiques utilisés pour l'analyse des données climatiques.
Les points sont organisés par région (Beauce et Bretagne).
"""

from typing import List, Dict, Tuple, Literal

# Points représentatifs - Beauce
BEAUCE_POINTS = [
    {"name": "Chartres", "lat": 48.45, "lon": 1.49, "region": "Beauce"},
    {"name": "Orléans", "lat": 47.90, "lon": 1.90, "region": "Beauce"},
    {"name": "Châteaudun", "lat": 48.07, "lon": 1.33, "region": "Beauce"},
]

# Points représentatifs - Bretagne
BRETAGNE_POINTS = [
    {"name": "Rennes", "lat": 48.11, "lon": -1.68, "region": "Bretagne"},
    {"name": "Brest", "lat": 48.39, "lon": -4.49, "region": "Bretagne"},
    {"name": "Vannes", "lat": 47.66, "lon": -2.76, "region": "Bretagne"},
]

# Tous les points combinés
ALL_POINTS = BEAUCE_POINTS + BRETAGNE_POINTS


def get_all_points(format: Literal["dict", "tuple", "lat_lon"] = "dict") -> List:
    """
    Retourne tous les points représentatifs dans le format demandé.
    
    Args:
        format: Format de retour souhaité
            - "dict": Liste de dictionnaires avec name, lat, lon, region
            - "tuple": Liste de tuples (lat, lon)
            - "lat_lon": Tuple de deux listes ([lats], [lons])
    
    Returns:
        Liste des points dans le format demandé
    """
    if format == "dict":
        return ALL_POINTS.copy()
    elif format == "tuple":
        return [(p["lat"], p["lon"]) for p in ALL_POINTS]
    elif format == "lat_lon":
        lats = [p["lat"] for p in ALL_POINTS]
        lons = [p["lon"] for p in ALL_POINTS]
        return (lats, lons)
    else:
        raise ValueError(f"Format non supporté: {format}")


def get_beauce_points(format: Literal["dict", "tuple", "lat_lon"] = "dict") -> List:
    """
    Retourne les points de la Beauce dans le format demandé.
    
    Args:
        format: Format de retour souhaité (voir get_all_points)
    
    Returns:
        Liste des points de la Beauce dans le format demandé
    """
    if format == "dict":
        return BEAUCE_POINTS.copy()
    elif format == "tuple":
        return [(p["lat"], p["lon"]) for p in BEAUCE_POINTS]
    elif format == "lat_lon":
        lats = [p["lat"] for p in BEAUCE_POINTS]
        lons = [p["lon"] for p in BEAUCE_POINTS]
        return (lats, lons)
    else:
        raise ValueError(f"Format non supporté: {format}")


def get_bretagne_points(format: Literal["dict", "tuple", "lat_lon"] = "dict") -> List:
    """
    Retourne les points de la Bretagne dans le format demandé.
    
    Args:
        format: Format de retour souhaité (voir get_all_points)
    
    Returns:
        Liste des points de la Bretagne dans le format demandé
    """
    if format == "dict":
        return BRETAGNE_POINTS.copy()
    elif format == "tuple":
        return [(p["lat"], p["lon"]) for p in BRETAGNE_POINTS]
    elif format == "lat_lon":
        lats = [p["lat"] for p in BRETAGNE_POINTS]
        lons = [p["lon"] for p in BRETAGNE_POINTS]
        return (lats, lons)
    else:
        raise ValueError(f"Format non supporté: {format}")


def get_point_by_name(name: str) -> Dict:
    """
    Retourne un point par son nom.
    
    Args:
        name: Nom du point (ex: "Chartres", "Rennes")
    
    Returns:
        Dictionnaire avec les informations du point
    
    Raises:
        ValueError: Si le point n'est pas trouvé
    """
    for point in ALL_POINTS:
        if point["name"].lower() == name.lower():
            return point.copy()
    raise ValueError(f"Point non trouvé: {name}")


def get_points_for_region(region: str, format: Literal["dict", "tuple", "lat_lon"] = "dict") -> List:
    """
    Retourne les points d'une région spécifique.
    
    Args:
        region: Nom de la région ("Beauce" ou "Bretagne")
        format: Format de retour souhaité
    
    Returns:
        Liste des points de la région dans le format demandé
    """
    if region.lower() == "beauce":
        return get_beauce_points(format)
    elif region.lower() == "bretagne":
        return get_bretagne_points(format)
    else:
        raise ValueError(f"Région non reconnue: {region}")

