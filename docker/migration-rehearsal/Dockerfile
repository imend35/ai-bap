# Build arguments are required so mutable image tags are never accepted by default.
ARG PYTHON_BASE_IMAGE
ARG UV_IMAGE
FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_BASE_IMAGE}
RUN groupadd --gid 10001 rehearsal \
    && useradd --uid 10001 --gid rehearsal --create-home --shell /usr/sbin/nologin rehearsal \
    && install --directory --owner=rehearsal --group=rehearsal --mode=0700 /run/secrets \
    && install --directory --owner=rehearsal --group=rehearsal --mode=0755 /run/rehearsal
WORKDIR /workspace/backend
COPY --from=uv /uv /uvx /bin/
COPY backend/pyproject.toml backend/uv.lock ./
# uv.lock is the source of truth; neither the application nor dev dependencies are installed.
RUN uv sync --locked --no-dev --no-install-project
COPY backend/migrations /workspace/migrations
COPY docker/migration-rehearsal/alembic.ini /workspace/rehearsal/alembic.ini
COPY docker/migration-rehearsal/env.py /workspace/migrations/env.py
COPY docker/migration-rehearsal/rehearse.py /workspace/rehearsal/rehearse.py
ENV PATH="/workspace/backend/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
ENTRYPOINT ["python", "/workspace/rehearsal/rehearse.py"]
