#!/usr/bin/env bash
# Pull the latest production image and recreate the Invisible Key app service.
# Run this on the Raspberry Pi from the checked-out repository.

set -euo pipefail

cd "$(dirname "$0")/.."

echo "Pulling latest git commit..."
git pull --ff-only origin main

echo "Pulling latest app image..."
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml pull app

echo "Recreating app container..."
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d --force-recreate app

echo
echo "Service status:"
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps

echo
echo "Recent app logs:"
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=80 app
