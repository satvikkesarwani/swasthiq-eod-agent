FROM node:25-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY frontend ./
RUN npm run build

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt ./
COPY backend/requirements.txt backend/requirements.txt
COPY backend/pyproject.toml backend/alembic.ini ./backend/
COPY backend/alembic ./backend/alembic
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./backend/app
COPY backend/scripts ./backend/scripts
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
COPY start.sh ./
RUN chmod +x start.sh backend/scripts/start.sh && chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

CMD ["./start.sh"]
