# ===== STAGE 1: Build Vue frontend =====
FROM node:20-alpine as frontend-build
WORKDIR /frontend
COPY sjhardware-frontend/package*.json ./
RUN npm install
COPY sjhardware-frontend/ ./
RUN npm run build

# ===== STAGE 2: Python + Flask backend =====
FROM python:3.11-slim

WORKDIR /app

# Install system deps + gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend
COPY . .

# Copy built Vue files into Flask static folder
COPY --from=frontend-build /frontend/dist ./app/static

# Use gunicorn in production
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]