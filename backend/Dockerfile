FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt pyproject.toml alembic.ini ./
COPY alembic ./alembic
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
RUN chmod +x scripts/start.sh && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

CMD ["./scripts/start.sh"]
