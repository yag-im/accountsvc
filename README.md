# accountsvc

Service managing user identities, profiles, and account lifecycle.

`accountsvc` is an asynchronous [FastAPI](https://fastapi.tiangolo.com/) microservice
built for cloud-native deployment. It ships with structured logging, OpenTelemetry
instrumentation, a fully typed codebase, a reproducible dependency lockfile, a
hardened non-root container image, and an automated semantic-release pipeline.

---

## Table of contents

- [Architecture](#architecture)
- [Project bootstrap](#project-bootstrap)
- [Local development](#local-development)
- [Running tests](#running-tests)
- [Linting](#linting)
- [Type checking](#type-checking)
- [Docker image build](#docker-image-build)
- [Configuration](#configuration)
- [Dependency management](#dependency-management)
- [Secret provisioning](#secret-provisioning)
- [Observability setup](#observability-setup)
- [Versioning and release flow](#versioning-and-release-flow)

---

## Architecture

The service is organised into strictly layered modules under `src/accountsvc`. Each
layer depends only on the layers below it — there are no reverse dependencies.

```text
api          HTTP transport: routing, request validation, serialization, error mapping
  │
services     Business logic and application workflows
  │
repositories Data access: SQLAlchemy queries against the database
  │
models       ORM entities (SQLAlchemy) and API contracts (Pydantic)

core         Cross-cutting concerns: configuration, logging, database engine,
             application lifespan, request context, observability helpers
```

Key design decisions:

- **Application factory.** `accountsvc.main:create_app` builds the app; there is no
  module-level global, which keeps imports side-effect free and tests isolated.
- **Dependency injection.** The persistence and service layers are wired together with
  FastAPI `Depends`, exposed as `Annotated` type aliases in
  [src/accountsvc/api/dependencies.py](src/accountsvc/api/dependencies.py).
- **Async everywhere.** SQLAlchemy 2.0 async engine with `psycopg` 3, async sessions,
  and async request handlers.
- **RFC 9457 errors.** All failures are serialized as `application/problem+json` via
  centralized exception handlers in [src/accountsvc/api/errors.py](src/accountsvc/api/errors.py).
- **Structured logs.** Every log line is single-line JSON enriched with the request id
  and the active OpenTelemetry trace/span ids (see
  [src/accountsvc/core/logging.py](src/accountsvc/core/logging.py)).
- **Health probes.** `GET /healthz` (liveness, no I/O) and `GET /readyz` (readiness,
  verifies database connectivity).

### API surface

| Method | Path                     | Description                         |
| ------ | ------------------------ | ----------------------------------- |
| GET    | `/healthz`               | Liveness probe                      |
| GET    | `/readyz`                | Readiness probe (checks database)   |
| GET    | `/users/{id}`            | Retrieve a user by id               |
| GET    | `/docs`                  | Swagger UI                          |
| GET    | `/openapi.json`          | OpenAPI schema                      |

---

## Project bootstrap

Requirements: [uv](https://docs.astral.sh/uv/) `0.11.32+`. uv provisions the correct
Python interpreter (3.14) automatically — no system Python setup is required.

```bash
make bootstrap
```

This resolves the lockfile (`uv lock`), creates the project virtualenv and installs
all dependencies (`uv sync`), and installs the git hooks (`pre-commit`).

> The fastest path to a fully configured environment is the included
> [devcontainer](.devcontainer/devcontainer.json): "Reopen in Container" runs the
> bootstrap automatically.

---

## Local development

```bash
make run          # start the service (uvicorn) using .env / secrets.env
```

By default local runs bind to `http://0.0.0.0:8091`. Interactive API docs are served
at `/docs`.

To debug, open the **Run and Debug** view and launch **FastAPI: uvicorn** (or
**FastAPI: uvicorn (reload)**). The devcontainer post-create hook provisions your local
`.vscode/settings.json` and `.vscode/launch.json` from the templates in
[.devcontainer/vscode](.devcontainer/vscode) when they are missing; both files are
git-ignored so personal tweaks stay local.

Common tasks are exposed through the [Makefile](Makefile):

| Command             | Description                                   |
| ------------------- | --------------------------------------------- |
| `make format`       | Auto-format and auto-fix with Ruff            |
| `make lint`         | Lint and check formatting                     |
| `make typecheck`    | Static type checking with Pyright             |
| `make test`         | Run the test suite                            |
| `make build`        | Build the wheel and sdist                     |
| `make docker-build` | Build the container image                     |
| `make audit`        | Scan locked dependencies for vulnerabilities  |
| `make run`          | Run the service locally                       |
| `make clean`        | Remove build artefacts and caches             |

---

## Running tests

```bash
make test
# or
uv run pytest
```

Integration tests run against the PostgreSQL database on
`sqldb.yag.dc` (the same engine version as production). The schema is expected to
already exist; tests only add and remove data. Each test executes inside a transaction
that is rolled back for complete isolation. The HTTP layer is exercised through
`httpx.ASGITransport` without binding a socket. `pytest-asyncio` runs in `auto`
mode, so async tests need no decorator.

---

## Linting

Linting and formatting are handled by [Ruff](https://docs.astral.sh/ruff/), configured
in [ruff.toml](ruff.toml) (single source of truth).
Ruff 0.16.0 or newer is required for the Python 3.14 target. Keep the
Ruff hook revision in [.pre-commit-config.yaml](.pre-commit-config.yaml)
aligned with the version in [uv.lock](uv.lock).

```bash
make lint     # ruff check . && ruff format --check .
make format   # ruff format . && ruff check --fix .
```

---

## Type checking

The codebase is fully type-annotated and checked with
[Pyright](https://microsoft.github.io/pyright/), configured in
[pyrightconfig.json](pyrightconfig.json).

```bash
make typecheck
# or
uv run pyright
```

---

## Docker image build

The [Dockerfile](Dockerfile) is a multi-stage build producing a minimal image that
runs as a non-root user (`uid 1001`) and binds unprivileged port `8080`.
The runtime stage applies available Debian updates and removes global pip and
its bundled installer wheel; application dependencies are installed in the builder.

```bash
make docker-build
# or, directly:
docker build --pull --build-arg APP_VERSION=0.1.0 -t accountsvc:local .
```

To reproduce the CI vulnerability gate locally with Trivy:

```bash
trivy image --scanners vuln --severity HIGH,CRITICAL \
  --ignore-unfixed --exit-code 1 accountsvc:local
```

Omit `--ignore-unfixed` to also report vulnerabilities with no published fix.
Rebuild with `--pull --no-cache` when checking for newly available base-image
and Debian updates; cached build layers do not rerun package updates.

Because the version is derived from git tags at build time (see
[versioning](#versioning-and-release-flow)) and the build context excludes `.git`, the
version is injected through the `APP_VERSION` build argument (which sets
`UV_DYNAMIC_VERSIONING_BYPASS`). Run the image with a database URL:

```bash
docker run --rm -p 8080:8080 \
  -e APP_DATABASE_URL=postgresql+psycopg://accountsvc:accountsvc@host.docker.internal:5432/accountsvc \
  accountsvc:local
curl http://localhost:8080/healthz
```

---

## Configuration

Configuration is provided by environment variables (prefix `APP_`) and, for
local development, the `.env` and `secrets.env` dotenv files. Settings are validated at
startup by [src/accountsvc/core/config.py](src/accountsvc/core/config.py); an invalid or
missing required value fails fast.

| Variable                              | Default        | Description                              |
| ------------------------------------- | -------------- | ---------------------------------------- |
| `APP_ENVIRONMENT`                     | `local`        | `local`/`dev`/`stage`/`prod`             |
| `APP_DB_HOST`                         | _(required)_   | Database host                            |
| `APP_DB_PORT`                         | `5432`         | Database port                            |
| `APP_DB_USER`                         | _(required)_   | Database user (set in `.env`)            |
| `APP_DB_PASSWORD`                     | _(required)_   | Database password (set in `secrets.env`) |
| `APP_DB_NAME`                         | _(required)_   | Database name                            |
| `APP_HOST`                            | `0.0.0.0`      | Bind address                             |
| `APP_PORT`                            | `8080`         | Bind port                                |
| `APP_LOG_LEVEL`                       | `INFO`         | Log level                                |
| `APP_DEBUG`                           | `false`        | Enable SQL echo and verbose behaviour    |
| `APP_DB_POOL_SIZE`                    | `5`            | Connection pool size                     |
| `APP_DB_MAX_OVERFLOW`                 | `10`           | Pool overflow capacity                   |
| `APP_DB_COMMAND_TIMEOUT_SECONDS`      | `30`           | Per-statement timeout                    |
| `APP_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS` | `30`         | Graceful shutdown window                 |

---

## Dependency management

Dependencies are managed exclusively with **uv** and pinned in `uv.lock` for
reproducible installs. Runtime dependencies live under `[project.dependencies]` and
development tools under `[dependency-groups] dev` (PEP 735) in
[pyproject.toml](pyproject.toml).

```bash
uv add <package>            # add a runtime dependency
uv add --dev <package>      # add a development dependency
uv lock --upgrade           # refresh the lockfile
uv sync --frozen            # install exactly what the lockfile specifies
make audit                  # pip-audit against the locked dependency set
```

---

## Secret provisioning

- **Local:** both `.env` and `secrets.env` are git-ignored and must be created
  manually after cloning. See the [Configuration](#configuration) table for all
  supported variables. At minimum, `secrets.env` must define
  `APP_DATABASE_URL` and `APP_TEST_DATABASE_URL`.
- **CI/CD:** GitHub Actions uses the built-in `GITHUB_TOKEN`; no long-lived secrets are
  stored for publishing to GHCR.
- **Deployed environments:** `APP_DATABASE_URL` and any other secrets are
  injected by the platform's secret manager as environment variables. Secrets are never
  committed or baked into the image.

---

## Observability setup

- **Structured logging.** JSON logs to stdout, correlated with `request_id` and
  OpenTelemetry `trace_id`/`span_id`. Health-check access logs are filtered out.
- **Request correlation.** `RequestContextMiddleware` honours or generates an
  `X-Request-ID` header and echoes it back on every response.
- **Tracing & metrics.** The container entrypoint is `opentelemetry-instrument`, which
  auto-instruments FastAPI, psycopg, and SQLAlchemy with zero code changes. Configure
  the collector via standard OTel environment variables, for example:

  ```bash
  OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
  OTEL_EXPORTER_OTLP_PROTOCOL=grpc
  OTEL_SERVICE_NAME=accountsvc
  ```

---

## Versioning and release flow

Versioning follows [Semantic Versioning](https://semver.org/) and is fully automated
from [Conventional Commits](https://www.conventionalcommits.org/).

- The package version is derived from git tags at build time by
  **uv-dynamic-versioning** — the version is never hand-edited.
- Pull request titles are validated against the Conventional Commits spec in CI.
- On merge to `main`, the [release workflow](.github/workflows/release.yml) runs
  **python-semantic-release**, which computes the next version, creates and pushes the
  `vX.Y.Z` git tag, and publishes a GitHub Release with generated notes.
- A new tag triggers a container build that is pushed to
  `ghcr.io/<owner>/accountsvc`, tagged with the immutable commit SHA and then promoted
  to the release version and `latest`. Images are built with SBOM and provenance
  attestations and scanned with Trivy.

Every push and pull request additionally runs the [CI workflow](.github/workflows/ci.yml)
(lint, type check, tests on Python 3.14, container build, and image scan).

---

## License

Distributed under the terms of the [GNU General Public License v3.0 or later](LICENSE).
