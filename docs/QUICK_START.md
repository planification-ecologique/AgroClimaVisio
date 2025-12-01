# Guide de démarrage rapide

## 📁 Emplacement des fichiers

Les fichiers NetCDF doivent être placés dans : **`backend/data/`**

## ✅ Configuration automatique

Le backend cherche automatiquement dans `backend/data/`. Aucune configuration supplémentaire n'est nécessaire.

## 🚀 Démarrer l'application

### Backend

```bash
cd backend
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur http://localhost:8000

### Frontend

```bash
cd frontend
yarn dev
```

L'application sera accessible sur http://localhost:5173

## 📊 Vérifier que les données sont chargées

Une fois le backend démarré, l'API utilisera automatiquement les fichiers dans `backend/data/` s'ils sont disponibles.

Pour vérifier :
1. Regardez les logs du backend
2. Vous devriez voir des messages indiquant si les fichiers sont trouvés
3. L'API retourne `"data_source": "real"` si les données réelles sont utilisées, sinon `"data_source": "mock"`

## 🔍 Structure attendue

```
backend/
├── data/
│   ├── prAdjust_*historical*.nc
│   ├── prAdjust_*ssp370*.nc
│   ├── tasAdjust_*historical*.nc  (optionnel)
│   └── tasmaxAdjust_*historical*.nc  (optionnel)
├── main.py
└── ...
```

## ⚙️ Configuration alternative

Si vous voulez utiliser un autre emplacement, créez `backend/.env` :

```env
CLIMATE_DATA_DIR=/chemin/absolu/vers/data
```

