#!/bin/bash
set -e

echo "Starting retail-backend app..."

# Generate env.json if not present
if [ ! -f /app/env.json ]; then
  echo "Generating env.json from environment variables..."
  cat > /app/env.json <<EOF
{
  "LOCAL_DB_URL": "postgresql://postgres:password1@localhost:5432/kimsphones",
  "DOCKER_DB_URL": "$(echo $DATABASE_URL)",
  "CLOUD_DB_URL": "${CLOUD_DB_URL:-}",
  "SECRET_KEY": "${SECRET_KEY:-supersecretkey}",
  "ENV": "production"
}
EOF
fi

# Run database migrations (Flask-Migrate / Alembic)
echo "Running database migrations..."
flask db upgrade || echo "Migrations failed or not needed"

# Start the app
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 run:app