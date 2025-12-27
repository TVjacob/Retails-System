# #!/bin/bash
# set -e

# echo "=== Building final clean image ==="
# TAG=198.38.82.197:5000/retail-backend:$(date +%s)
# docker build --no-cache -t $TAG -t 198.38.82.197:5000/retail-backend:latest .
# docker push 198.38.82.197:5000/retail-backend:latest

# echo "=== Stopping old container ==="
# docker stop retail-backend 2>/dev/null || true
# docker rm -f retail-backend 2>/dev/null || true

# echo "=== Starting new container — NO VOLUME MOUNT NEEDED ==="
# docker run -d \
#   --name retail-backend \
#   --restart always \
#   -p 8980:5000 \
#   --network myapp-net \
#   -e DATABASE_URL="postgresql://postgres:password1@my_postgres:5432/kimsphones" \
#   -e SECRET_KEY="supersecretkey" \
#   198.38.82.197:5000/retail-backend:latest

# echo ""
# echo "=================================================================="
# echo " SUCCESS — YOUR APP IS LIVE!"
# echo " Access it at: http://tukibube.it.com:8980"
# echo "=================================================================="
#!/bin/bash
set -e

if [ ! -f /app/env.json ]; then
  echo "No env.json found — generating default one..."
  cat > /app/env.json <<EOF
{
  "LOCAL_DB_URL": "postgresql://postgres:password1@localhost:5432/kimsphones",
  "DOCKER_DB_URL": "postgresql://postgres:password1@my_postgres:5432/kimsphones",
  "CLOUD_DB_URL": "${CLOUD_DB_URL:-}",
  "SECRET_KEY": "${SECRET_KEY:-supersecretkey}",
  "ENV": "${ENV:-production}"
}
EOF
fi

flask db upgrade 2>/dev/null || true

exec "$@"