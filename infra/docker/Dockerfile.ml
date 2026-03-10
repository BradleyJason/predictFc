FROM python:3.11-slim

WORKDIR /app

# Installer Poetry + DVC
RUN pip install poetry dvc --break-system-packages

# Copier les fichiers de dépendances
COPY ml/pyproject.toml ./
COPY ml/poetry.lock* ./

# Installer les dépendances
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction

# Copier le code
COPY ml/ .

CMD ["python", "pipelines/ingest.py"]
