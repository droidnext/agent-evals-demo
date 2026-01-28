#!/bin/bash
# Start Phoenix Arize using Docker Compose

echo "================================"
echo "Starting Phoenix Arize (Docker)"
echo "================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    echo ""
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT/phoenix-arize"

echo "1️⃣  Starting Phoenix with Docker Compose..."
echo ""

# Start Phoenix using docker-compose
docker compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Phoenix Arize started successfully!"
    echo ""
    echo "================================"
    echo "Phoenix UI: http://localhost:6006"
    echo "OTLP gRPC:  localhost:4317"
    echo "Prometheus: localhost:9090"
    echo "================================"
    echo ""
    echo "Default credentials:"
    echo "  Username: admin@example.com"
    echo "  Password: admin"
    echo ""
    echo "To stop: ./scripts/stop_phoenix.sh"
    echo "To view logs: docker compose -f phoenix-arize/docker-compose.yml logs -f"
else
    echo ""
    echo "❌ Failed to start Phoenix"
    exit 1
fi

echo ""
