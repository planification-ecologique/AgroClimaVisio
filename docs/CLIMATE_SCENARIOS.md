# Scénarios climatiques (SSP)

## Qu'est-ce qu'un scénario SSP ?

Les **Shared Socioeconomic Pathways (SSP)** sont des scénarios utilisés par le GIEC (IPCC) pour projeter l'évolution du climat au 21ème siècle. Ils combinent :
- Des **trajectoires d'émissions de gaz à effet de serre** (RCP - Representative Concentration Pathways)
- Des **scénarios socio-économiques** (SSP)

## Structure des codes SSP

Les codes suivent le format : **SSP{X}-{Y}.{Z}**

- **SSP{X}** : Numéro du scénario socio-économique (1 à 5)
- **{Y}.{Z}** : Forçage radiatif en W/m² (niveau de réchauffement)

## Scénarios disponibles dans les données Météo-France

### SSP1-2.6 (ssp126)
- **Forçage radiatif** : 2.6 W/m²
- **Description** : Scénario optimiste
- **Caractéristiques** :
  - Réduction rapide des émissions
  - Transition énergétique rapide
  - Réchauffement limité à ~1.5-2°C d'ici 2100
- **Utilisation** : Scénario de référence pour les objectifs de l'Accord de Paris

### SSP2-4.5 (ssp245)
- **Forçage radiatif** : 4.5 W/m²
- **Description** : Scénario intermédiaire
- **Caractéristiques** :
  - Émissions modérées
  - Réchauffement d'environ 2.5-3°C d'ici 2100
- **Utilisation** : Scénario "business as usual" modéré

### SSP3-7.0 (ssp370)
- **Forçage radiatif** : 7.0 W/m²
- **Description** : Scénario pessimiste
- **Caractéristiques** :
  - Émissions élevées
  - Développement inégal entre régions
  - Réchauffement d'environ 3.5-4.5°C d'ici 2100
- **Utilisation** : Scénario utilisé par défaut dans AgroClimaVisio
- **Pourquoi ce scénario ?** : Il représente un scénario réaliste si les efforts de réduction des émissions ne sont pas suffisants

### SSP5-8.5 (ssp585)
- **Forçage radiatif** : 8.5 W/m²
- **Description** : Scénario très pessimiste
- **Caractéristiques** :
  - Émissions très élevées
  - Croissance économique forte basée sur les combustibles fossiles
  - Réchauffement d'environ 4-6°C d'ici 2100
- **Utilisation** : Scénario "worst case" pour évaluer les risques extrêmes

## Comparaison des scénarios

| Scénario | Code | Forçage (W/m²) | Réchauffement 2100 | Émissions |
|----------|------|----------------|-------------------|-----------|
| SSP1-2.6 | ssp126 | 2.6 | ~1.5-2°C | Faibles |
| SSP2-4.5 | ssp245 | 4.5 | ~2.5-3°C | Modérées |
| SSP3-7.0 | ssp370 | 7.0 | ~3.5-4.5°C | Élevées |
| SSP5-8.5 | ssp585 | 8.5 | ~4-6°C | Très élevées |

## Scénario "historical"

Le scénario **historical** contient les données observées du passé (généralement 1950-2014). Il sert de :
- **Référence** pour comparer les projections futures
- **Validation** des modèles climatiques
- **Base** pour comprendre l'évolution passée du climat

## Quel scénario utiliser ?

### Pour AgroClimaVisio

**Recommandation** : Utiliser **SSP3-7.0 (ssp370)** comme scénario par défaut car :
1. Il représente un scénario réaliste si les efforts actuels continuent
2. Il permet d'évaluer les risques agricoles de manière préventive
3. Il est largement disponible dans les données Météo-France

### Pour des analyses spécifiques

- **Analyse optimiste** : Utiliser SSP1-2.6 (ssp126)
- **Analyse de référence** : Utiliser SSP2-4.5 (ssp245)
- **Analyse de risque** : Utiliser SSP3-7.0 (ssp370)
- **Analyse de pire cas** : Utiliser SSP5-8.5 (ssp585)

## Impact sur les indicateurs agricoles

### Températures
- **ssp126** : Augmentation modérée, adaptation possible
- **ssp370** : Augmentation significative, stress thermique fréquent
- **ssp585** : Augmentation très forte, conditions extrêmes

### Précipitations
- **ssp126** : Changements modérés, saisonnalité préservée
- **ssp370** : Changements marqués, sécheresses plus fréquentes
- **ssp585** : Changements extrêmes, événements violents fréquents

### Risques agricoles
- **ssp126** : Risques modérés, adaptation possible
- **ssp370** : Risques élevés, nécessite des stratégies d'adaptation
- **ssp585** : Risques très élevés, transformation nécessaire des systèmes agricoles

## Références

- **GIEC (IPCC)** : 6ème rapport d'évaluation (AR6)
- **Météo-France** : Projections climatiques DRIAS
- **CMIP6** : Coupled Model Intercomparison Project Phase 6

## Liens utiles

- [IPCC AR6 Scenarios](https://www.ipcc.ch/report/ar6/wg1/)
- [DRIAS - Les futurs du climat](https://www.drias-climat.fr/)
- [Documentation Météo-France](https://guides.data.gouv.fr/guide-du-participant-au-hackathon-le-climat-en-donnees/)

