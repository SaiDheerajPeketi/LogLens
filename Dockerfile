FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LOGLENS_ENVIRONMENT=production \
    LOGLENS_DATABASE_URL=sqlite:////app/data/runtime/loglens.sqlite3 \
    LOGLENS_MODEL_DIR=/app/artifacts/models \
    LOGLENS_STATIC_DIR=/app/frontend/dist

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY backend/ ./backend/
COPY artifacts/models/ ./artifacts/models/
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
RUN python -m pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 loglens \
    && mkdir -p /app/data/runtime \
    && chown -R loglens:loglens /app/data

USER loglens
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=4 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/v1/health', timeout=2)"

CMD ["uvicorn", "loglens.main:app", "--host", "0.0.0.0", "--port", "8080"]
