#!/bin/bash
# Stop Phoenix Arize Docker container

echo "================================"
echo "Stopping Phoenix Arize (Docker)"
echo "================================"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT/phoenix-arize"

echo "1️⃣  Stopping Phoenix container..."
echo ""

# Stop Phoenix using docker-compose
docker compose down

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Phoenix stopped successfully"
else
    echo ""
    echo "⚠️  Error stopping Phoenix"
fi

echo ""
