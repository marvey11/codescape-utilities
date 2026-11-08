# ==========================================
# Stage 1: Build & Dependency Resolution
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

# Install Git so uv can fetch Git-based dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt-get/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Copy the app lockfile and package manifests.
COPY apps/audiothek-downloader/pyproject.toml apps/audiothek-downloader/uv.lock apps/audiothek-downloader/README.md ./apps/audiothek-downloader/
COPY libs/core/pyproject.toml libs/core/README.md ./libs/core/
COPY libs/core/src ./libs/core/src

# Pre-install third-party & Git dependencies (cached unless uv.lock / pyproject.toml changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --project apps/audiothek-downloader \
    --locked \
    --no-dev \
    --no-editable \
    --no-install-project

# Copy the app source before installing the project.
COPY apps/audiothek-downloader/src ./apps/audiothek-downloader/src

# Fast sync to install audiothek-downloader itself into .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --project apps/audiothek-downloader \
    --locked \
    --no-dev \
    --no-editable

# ==========================================
# Stage 2: Production Runtime
# ==========================================
FROM python:3.14-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Create a non-root user for runtime security
RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

# Copy installed virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Define volume mount points
VOLUME ["/data", "/podcasts"]

USER appuser

ENTRYPOINT ["audiothek-downloader"]
CMD ["--application-data-dir", "/data", "--podcast-storage-dir", "/podcasts"]
