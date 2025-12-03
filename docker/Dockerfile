FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Set venv location to avoid conflicts with volume mounts
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Copy dependency files and README (needed for package build)
# Note: Build context should be the project root
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync

# Copy the rest of the application
COPY . .

