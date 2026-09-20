# ==========================================
# Stage 1: Build & Dependency Resolution
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Install Git so uv can fetch Git-based dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt-get/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy lockfile and package manifests
COPY pyproject.toml uv.lock ./
COPY apps/audiothek-downloader/pyproject.toml apps/audiothek-downloader/README.md ./apps/audiothek-downloader/

# Pre-install third-party & Git dependencies (cached unless uv.lock / pyproject.toml changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --frozen \
    --no-dev \
    --no-editable \
    --no-install-workspace \
    --package audiothek-downloader

# Copy full source code for workspace packages
COPY apps/audiothek-downloader/src ./apps/audiothek-downloader/src

# Fast sync to install audiothek-downloader itself into .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
    --frozen \
    --no-dev \
    --no-editable \
    --package audiothek-downloader

# ==========================================
# Stage 2: Production Runtime
# ==========================================
FROM python:3.12-slim-bookworm AS runtime

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
