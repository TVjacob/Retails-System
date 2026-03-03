#!/bin/bash
# render-build.sh – Perfect build script for Render

set -e  # Stop on any error

echo "Installing Python packages..."
pip install -r requirements.txt gunicorn

echo "Building Vue frontend..."
cd sjhardware-frontend

# Use Node version from package.json
npm ci --only=production   # faster & cleaner
npm run build

echo "Copying built Vue files to Flask static folder..."
cd ..
rm -rf static app/static
mkdir -p static
cp -r sjhardware-frontend/dist/* static/

echo "SJ Hardware frontend built and copied successfully!"
echo "Files in static/:"
ls -la static/