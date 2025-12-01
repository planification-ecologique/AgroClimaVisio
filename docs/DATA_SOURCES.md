# Sources de données climatiques

## Données Météo-France SOCLE Métropole

L'API utilise les données de projections climatiques du projet SOCLE Métropole de Météo-France, disponibles dans le cadre du hackathon "Le climat en données" 2025.

### Documentation
- **Guide des données** : https://guides.data.gouv.fr/guide-du-participant-au-hackathon-le-climat-en-donnees/ressources-du-hackathon/donnees/donnees-de-projections-climatiques
- **Accès aux données** : https://console.object.files.data.gouv.fr/browser/meteofrance-drias/SocleM-Climat-2025%2F

### Variables disponibles

| Code | Nom | Unité | Description |
|------|-----|-------|-------------|
| `tas` | Température moyenne à 2 mètres | K | Température moyenne de l'atmosphère à 2 mètres |
| `tasmin` | Température minimale à 2 mètres | K | Température minimale de l'atmosphère à 2 mètres |
| `tasmax` | Température maximale à 2 mètres | K | Température maximale de l'atmosphère à 2 mètres |
| `pr` | Précipitations | kg/m²/s | Précipitation moyenne (inclut pluie et neige) |
| `rsds` | Rayonnement solaire incident | W/m² | Rayonnement solaire incident (descendant) en surface |
| `rlds` | Rayonnement infrarouge incident | W/m² | Rayonnement infrarouge incident (descendant) en surface |
| `huss` | Humidité spécifique | kg/kg | Humidité spécifique moyenne de l'atmosphère à 2 mètres |
| `sfcWind` | Vitesse du vent | m/s | Vitesse du vent moyen à 10 mètres |

### Scénarios climatiques

- `historical` : Données historiques (1950-2014)
- `ssp126` : Scénario optimiste (réchauffement limité)
- `ssp245` : Scénario intermédiaire
- `ssp370` : Scénario pessimiste (émissions élevées)
- `ssp585` : Scénario très pessimiste (émissions très élevées)

### Résolutions disponibles

- **8 km** : Données RCM (Regional Climate Model) - Données quotidiennes
- **2.5 km** : Données CPRCM (Convection-Permitting RCM) - Données horaires pour précipitations

### Méthodes de descente d'échelle

1. **RCM** : Modèles climatiques régionaux (~12 km, ajustés à 8 km)
2. **CPRCM** : Modèles régionaux kilométriques (haute résolution)
3. **EMULATEUR** : Méthode d'émulation statistique (10 membres d'ensemble)

### Jeux de données disponibles

62 jeux de données au total, combinant :
- Différents modèles globaux (GCM) : CNRM-ESM2-1, NorESM2-MM, IPSL-CM6A-LR, etc.
- Différents modèles régionaux (RCM) : CNRM-ALADIN64E1, HCLIM43-ALADIN, RACMO23E, etc.
- Différents scénarios et membres d'ensemble

## Endpoints API disponibles

### `/api/variables`
Liste toutes les variables climatiques disponibles avec leurs descriptions.

### `/api/experiments`
Liste tous les scénarios climatiques disponibles.

### `/api/datasets`
Liste les jeux de données disponibles avec filtres optionnels :
- `?variable=pr` : Filtrer par variable
- `?experiment=ssp370` : Filtrer par scénario
- `?start_year=2020&end_year=2050` : Filtrer par période

### `/api/datasets/summary`
Résumé statistique des données disponibles.

## Utilisation pour AgroClimaVisio

### Variables utiles pour les indicateurs agricoles

**Potentiel agro-climatique** :
- `pr` : Précipitations totales
- `tas` : Températures moyennes
- `rsds` : Rayonnement solaire (pour les degrés-jours)

**Risque de sécheresse** :
- `pr` : Jours consécutifs sans pluie
- Cumul de précipitations

**Risque d'excès d'eau** :
- `pr` : Précipitations cumulées sur 7 jours
- Jours avec précipitations > seuil

**Extrêmes et vagues de chaleur** :
- `tasmax` : Jours avec température > 30°C ou 35°C
- `pr` : Événements de pluie extrême

### Prochaines étapes

1. **Chargement des données NetCDF** : Utiliser `xarray` ou `rasterio` pour lire les fichiers NetCDF
2. **Calcul des indicateurs** : Implémenter les calculs d'indicateurs agro-climatiques
3. **Agrégation spatiale** : Agréger les données à 8 km vers des polygones administratifs ou agricoles
4. **Cache** : Mettre en cache les résultats de calcul pour améliorer les performances

