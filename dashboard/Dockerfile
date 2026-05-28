# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=dev || npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq5 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY backend ./backend
COPY alembic ./alembic
COPY alembic.ini ./
COPY --from=frontend-build /app/frontend/dist ./static
EXPOSE 7421
ENV PYTHONUNBUFFERED=1
# entrypoint: uvicorn backend.main:app --host 0.0.0.0 --port 7421
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7421"]
