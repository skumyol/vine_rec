#!/bin/bash

set -e

# Parse arguments
CHECK_ONLY=false
if [ "$1" = "--check" ]; then
    CHECK_ONLY=true
fi

echo "=== Wine Photo Verification - Production Mode ==="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Check if services are already running
check_services() {
    if docker compose ps --format json 2>/dev/null | grep -q "running"; then
        return 0
    fi
    return 1
}

if [ "$CHECK_ONLY" = true ]; then
    if check_services; then
        echo "Production services are running"
        docker compose ps
        exit 0
    else
        echo "Production services are not running"
        exit 1
    fi
fi

# Load environment
if [ -f .env ]; then
    echo "Loading environment from .env"
    export $(grep -v '^#' .env | xargs)
fi

# Build and start
echo "Building and starting production services..."
docker compose -f docker-compose.yml up --build -d

echo ""
echo "=== Production services started ==="
docker compose ps

echo ""
echo "Services available at:"
echo "- Frontend: http://localhost"
echo "- API: http://localhost/api"
echo "- API Docs: http://localhost/docs"
