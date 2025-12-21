#!/bin/bash
set -e

# If env.json is mounted from host (Jenkins does this), keep it
# Otherwise generate a default one from environment variables
if [ ! -f /app/env.json ]; then
  echo "No env.json found — generating default one..."
  cat > /app/env.json <<EOF
{
  "LOCAL_DB_URL": "postgresql://postgres:password1@localhost:5432/retail",
  "DOCKER_DB_URL": "postgresql://postgres:password1@localhost:5432/retail",
  "CLOUD_DB_URL": "${CLOUD_DB_URL:-postgresql://sj_user:password@prod-db-host/sjhardware}",
  "SECRET_KEY": "${SECRET_KEY:-supersecretkey}",
  "ENV": "${ENV:-production}"
}
EOF
fi

# Run database migrations if you have Flask-Migrate
flask db upgrade 2>/dev/null || true

# Start the app
exec "$@"