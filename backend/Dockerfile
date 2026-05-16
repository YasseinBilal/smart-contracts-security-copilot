FROM python:3.12-slim

WORKDIR /app

# Install system deps needed by Slither (solc, git) and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Install solc-select to manage Solidity compiler versions
RUN pip install solc-select && solc-select install 0.8.20 && solc-select use 0.8.20

# Copy dependency manifest and install deps before copying source (layer caching)
COPY pyproject.toml .
RUN uv sync --no-dev

COPY . .

# Run migrations then start server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
