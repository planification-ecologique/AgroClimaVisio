# Choix techniques à faire

## ✅ Choix déjà effectués

- **Frontend**: Vite + React + TypeScript
- **Cartes**: MapLibre GL
- **Backend**: FastAPI (Python)
- **Style de carte de base**: OpenStreetMap (tiles raster)

## ❓ Choix techniques à décider

### 1. Source de données climatiques

**Question**: Comment allez-vous intégrer les données de projections climatiques de Météo-France ?

**Options possibles**:
- Fichiers NetCDF locaux
- API Météo-France (si disponible)
- Base de données PostgreSQL/PostGIS avec données pré-traitées
- Fichiers GeoJSON/Shapefile pré-calculés

**Recommandation**: Base de données PostgreSQL/PostGIS pour de meilleures performances sur de grandes quantités de données géospatiales.

---

### 2. Format de stockage des données climatiques

**Question**: Quel format pour les données climatiques projetées ?

**Options possibles**:
- NetCDF (standard météorologique)
- GeoJSON (simple mais peut être volumineux)
- Tiles vectorielles (Mapbox Vector Tiles)
- Base de données avec PostGIS

**Recommandation**: Tiles vectorielles pour de meilleures performances de visualisation, ou PostgreSQL/PostGIS pour le traitement.

---

### 3. Bibliothèque de traitement des données géospatiales

**Question**: Quelle bibliothèque Python pour traiter les données géospatiales ?

**Options possibles**:
- `rasterio` + `xarray` (pour NetCDF)
- `geopandas` (pour données vectorielles)
- `shapely` (pour géométries)
- `pyproj` (pour projections)

**Recommandation**: `geopandas` + `rasterio` + `xarray` selon le format des données.

---

### 4. Style de carte

**Question**: Quel style de carte souhaitez-vous utiliser ?

**Options possibles**:
- OpenStreetMap (actuellement utilisé)
- Cartes topographiques IGN (si disponible)
- Style personnalisé MapLibre
- Satellite (si nécessaire)

**Recommandation**: Garder OpenStreetMap pour le développement, puis envisager un style personnalisé ou IGN pour la production.

---

### 5. Calcul des indicateurs

**Question**: Où calculer les indicateurs agro-climatiques ?

**Options possibles**:
- Backend (calcul à la volée)
- Pré-calcul et stockage en base de données
- Calcul côté client (WebAssembly)

**Recommandation**: Pré-calcul pour de meilleures performances, avec possibilité de recalcul à la volée pour des paramètres personnalisés.

---

### 6. Gestion de l'authentification

**Question**: Avez-vous besoin d'authentification utilisateur ?

**Options possibles**:
- Pas d'authentification (accès public)
- Authentification simple (tokens JWT)
- OAuth2 / OIDC

**Recommandation**: Commencer sans authentification, ajouter si nécessaire.

---

### 7. Export de cartes

**Question**: Comment exporter les cartes ?

**Options possibles**:
- PNG via MapLibre
- PDF (nécessite une bibliothèque supplémentaire)
- GeoJSON des données affichées
- CSV des statistiques

**Recommandation**: PNG pour les images, GeoJSON pour les données.

---

### 8. Mode comparaison

**Question**: Comment implémenter le mode comparaison ?

**Options possibles**:
- Deux cartes côte à côte
- Carte avec slider pour basculer entre années
- Carte avec overlay (transparence)
- Animation temporelle

**Recommandation**: Carte avec slider ou deux cartes côte à côte selon la préférence UX.

---

### 9. Légende et échelle de couleurs

**Question**: Quelle échelle de couleurs pour les cartes ?

**Options possibles**:
- Échelles prédéfinies (viridis, plasma, etc.)
- Échelles personnalisées par type de carte
- Échelles adaptatives selon les données

**Recommandation**: Échelles personnalisées par type de carte avec possibilité d'ajustement.

---

### 10. Performance et cache

**Question**: Comment gérer le cache des données ?

**Options possibles**:
- Redis pour le cache API
- Cache HTTP (CDN)
- Cache côté client (IndexedDB)
- Pas de cache (pour commencer)

**Recommandation**: Commencer sans cache, ajouter Redis si nécessaire pour les performances.

---

## 📝 Prochaines étapes recommandées

1. **Définir la source de données** - C'est le point le plus critique
2. **Choisir le format de stockage** - Dépend de la source
3. **Implémenter le calcul des indicateurs** - Une fois les données disponibles
4. **Ajouter les couches sur la carte** - Une fois les données calculées
5. **Implémenter le mode comparaison** - Amélioration UX
6. **Ajouter l'export** - Fonctionnalité utile

