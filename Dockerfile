FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# pg_dump 17 para los backups, desde el repositorio oficial de PostgreSQL.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-common \
    && /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y \
    && apt-get install -y --no-install-recommends postgresql-client-17 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 app && mkdir /app/backups && chown app:app /app /app/backups
COPY --chown=app:app . .
USER app
RUN DJANGO_SECRET_KEY=build-only-placeholder-not-a-deployment-secret-000000000000 python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
