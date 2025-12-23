#!/bin/bash
set -e

echo "=== Building final clean image ==="
TAG=198.38.82.197:5000/retail-backend:$(date +%s)
docker build --no-cache -t $TAG -t 198.38.82.197:5000/retail-backend:latest .
docker push 198.38.82.197:5000/retail-backend:latest

echo "=== Stopping old container ==="
docker stop retail-backend 2>/dev/null || true
docker rm -f retail-backend 2>/dev/null || true

echo "=== Starting new container — NO VOLUME MOUNT NEEDED ==="
docker run -d \
  --name retail-backend \
  --restart always \
  -p 8980:5000 \
  --network myapp-net \  # Make sure this network exists: docker network create myapp-net if not
  -e DATABASE_URL="postgresql://postgres:password1@my_postgres:5432/kimsphones" \
  -e SECRET_KEY="supersecretkey" \
  198.38.82.197:5000/retail-backend:latest

echo ""
echo "=================================================================="
echo " SUCCESS — YOUR APP IS LIVE!"
echo " Access it at: http://tukibube.it.com:8980 (or your server IP:8980)"
echo "=================================================================="