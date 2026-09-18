FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies for PostgreSQL, cryptography, and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for ultra-fast dependency resolution
RUN pip install --no-cache-dir uv gunicorn

# Copy pyproject.toml and lockfile if present
COPY pyproject.toml uv.lock* ./

# Install project dependencies
RUN uv pip install --system -r pyproject.toml

# Copy project source code
COPY . .

EXPOSE 8000

CMD ["gunicorn", "wger.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
