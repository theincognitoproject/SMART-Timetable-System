FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pkg-config \
    libmariadb-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements first
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set non-sensitive defaults
ENV DB_PORT=3306
ENV DB_HOST=localhost

# Copy backend code
COPY backend/ .

# Ensure .env is not copied into image for security
# Instead use docker-compose env_file or runtime environment variables

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
