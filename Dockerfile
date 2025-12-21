# ===== STAGE 1: Build Vue frontend =====
FROM node:20-alpine as frontend-build
WORKDIR /frontend
COPY retail-service-shop-frontend/package*.json ./
RUN npm install
COPY retail-service-shop-frontend/ ./
RUN npm run build

# ===== STAGE 2: Python + Flask backend =====
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend source code
COPY . .

# Copy built Vue frontend
COPY --from=frontend-build /frontend/dist ./app/static

# Copy entrypoint script for generating env.json dynamically
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Environment
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Use our entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
