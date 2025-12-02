# Utiliser une image Python officielle avec les bibliothèques système nécessaires
FROM python:3.12-slim

# Installer les dépendances système nécessaires pour DuckDB et NetCDF
RUN apt-get update && \
    apt-get install -y \
    gcc \
    g++ \
    libstdc++6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Installer Poetry 2.0.0 (même version que localement)
RUN pip install poetry==2.0.0

# Configurer Poetry pour ne pas créer d'environnement virtuel (on utilise le système)
RUN poetry config virtualenvs.create false

# Copier d'abord uniquement les fichiers de configuration Poetry (pour optimiser le cache Docker)
COPY backend/pyproject.toml backend/poetry.lock ./backend/

# Installer les dépendances Python (cette couche sera mise en cache si pyproject.toml ne change pas)
WORKDIR /app/backend
# Régénérer le lock file si nécessaire (si pyproject.toml a changé), puis installer
RUN poetry lock --no-update 2>/dev/null || poetry lock || true && \
    poetry install --without dev --no-interaction --no-ansi
WORKDIR /app

# Copier le reste du code backend
COPY backend/ ./backend/

# Exposer le port (Railway utilisera la variable d'environnement PORT)
EXPOSE 8080

# Utiliser la variable d'environnement PORT de Railway (par défaut 8080)
ENV PORT=8080

# Configurer PYTHONPATH pour que Python trouve les modules backend
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Commande de démarrage avec support de la variable PORT
# Lancer depuis /app/backend pour que les imports relatifs fonctionnent
WORKDIR /app/backend
CMD sh -c "python -m uvicorn main:app --host 0.0.0.0 --port \${PORT:-8080}"

