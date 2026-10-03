# syntax=docker/dockerfile:1.9

ARG PYTHON_VERSION=3.14

##########################################################################
# Builder: resolve and install dependencies, then the project itself.
##########################################################################
FROM python:${PYTHON_VERSION}-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# Install third-party dependencies first. This layer is cached and only
# invalidated when pyproject.toml or uv.lock change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --frozen --no-dev --no-install-project

# Install the project. uv-dynamic-versioning derives the version from git tags,
# which are unavailable in the build context, so the version is injected instead.
ARG APP_VERSION=0.0.0
ENV UV_DYNAMIC_VERSIONING_BYPASS=${APP_VERSION}
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

##########################################################################
# Runtime: minimal image running as a non-root user on port 8080.
##########################################################################
FROM python:${PYTHON_VERSION}-slim AS runtime

ARG APP_VERSION=0.0.0
ARG GIT_SHA=unknown
ARG BUILD_TIMESTAMP=unknown

LABEL org.opencontainers.image.title="accountsvc" \
    org.opencontainers.image.description="Service managing user identities, profiles, and account lifecycle." \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.revision="${GIT_SHA}" \
    org.opencontainers.image.created="${BUILD_TIMESTAMP}" \
    org.opencontainers.image.licenses="GPL-3.0-or-later" \
    org.opencontainers.image.source="https://github.com/yag-im/accountsvc"

RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    OTEL_SERVICE_NAME=accountsvc

EXPOSE 8080
STOPSIGNAL SIGTERM
USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).status == 200 else 1)"]

# opentelemetry-instrument provides zero-code tracing/metrics for the service.
ENTRYPOINT ["opentelemetry-instrument"]
CMD ["accountsvc"]
