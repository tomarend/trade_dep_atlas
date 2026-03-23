FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for duckdb and other native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and source first for layer caching
COPY pyproject.toml .
COPY pipeline/ ./pipeline/
COPY dashboard/ ./dashboard/

# Install the project and its dependencies
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir -e .

# Copy remaining project files
COPY . .

# Create data directory (pipeline writes here; mount a volume in production)
RUN mkdir -p data

EXPOSE 8050

# Use 1 worker — DuckDB module-level singleton is process-specific
# Mount data/ as a Docker volume in production to persist the DuckDB file
CMD ["gunicorn", "dashboard.app:server", "--bind", "0.0.0.0:8050", "--workers", "1", "--timeout", "120"]
