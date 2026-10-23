FROM ghcr.io/astral-sh/uv:0.6.10 AS uv

FROM python:3.13-slim

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./alembic.ini
COPY docker/backend/initialize_fresh_database.py /usr/local/bin/initialize_fresh_database.py
COPY docker/backend/migrate_production.py /usr/local/bin/migrate_production.py
COPY docker/backend/start_api.py /usr/local/bin/start_api.py
COPY docker/backend/start_api_free.py /usr/local/bin/start_api_free.py
COPY docker/backend/bootstrap_initial_admin_from_environment.py /usr/local/bin/bootstrap_initial_admin_from_environment.py

RUN chown -R app:app /app /usr/local/bin/initialize_fresh_database.py /usr/local/bin/migrate_production.py /usr/local/bin/start_api.py /usr/local/bin/start_api_free.py /usr/local/bin/bootstrap_initial_admin_from_environment.py

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 10001:10001

EXPOSE 8000

CMD ["python", "/usr/local/bin/start_api.py"]
