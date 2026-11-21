# TaxSaint Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including C++ compiler for on-demand tax engine compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Set python path so all packages resolve cleanly
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "integration.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
