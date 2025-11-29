# AgroClimaVisio Frontend

Frontend React + Vite + TypeScript pour AgroClimaVisio.

## Prérequis

- Node.js 20+ (voir [installation](https://nodejs.org/))
- Yarn 1.22+ (voir [installation](https://yarnpkg.com/getting-started/install))

Si vous utilisez `nvm`, vous pouvez utiliser le fichier `.nvmrc` :
```bash
nvm use
```

## Installation

```bash
yarn install
```

## Démarrage en développement

```bash
yarn dev
```

L'application sera accessible sur http://localhost:5173

## Build pour production

```bash
yarn build
```

Les fichiers de production seront dans le dossier `dist/`.

## Prévisualisation du build

```bash
yarn preview
```

## Commandes Yarn utiles

- `yarn add <package>` - Ajouter une dépendance
- `yarn add -D <package>` - Ajouter une dépendance de développement
- `yarn remove <package>` - Supprimer une dépendance
- `yarn upgrade` - Mettre à jour les dépendances
- `yarn lint` - Lancer le linter

## Structure

- `src/components/` - Composants React
  - `Header.tsx` - En-tête avec sélection d'année et contrôles
  - `ParametersPanel.tsx` - Panneau de paramètres
  - `Map.tsx` - Composant de carte MapLibre
- `src/types.ts` - Types TypeScript
- `src/App.tsx` - Composant principal

## Configuration

Créez un fichier `.env` basé sur `.env.example` pour configurer l'URL de l'API backend.
