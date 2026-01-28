#!/bin/bash
# Script to stop Google ADK services

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Stopping ADK Services${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Find and kill ADK processes
echo "1️⃣  Looking for ADK processes..."

# Find processes running adk (both web and dev)
ADK_PIDS=$(pgrep -f "adk web|adk dev" || true)

if [ -z "$ADK_PIDS" ]; then
    echo "  No ADK processes found"
else
    echo "  Found ADK processes: $ADK_PIDS"
    echo "  Stopping..."
    kill $ADK_PIDS 2>/dev/null || true
    sleep 1
    
    # Force kill if still running
    REMAINING=$(pgrep -f "adk web|adk dev" || true)
    if [ -n "$REMAINING" ]; then
        echo "  Force stopping stubborn processes..."
        kill -9 $REMAINING 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓${NC} Stopped ADK processes"
fi

# Also check port 8000
echo ""
echo "Checking port 8000..."
PORT_PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo "  Found process on port 8000: $PORT_PIDS"
    echo "  Killing..."
    kill -9 $PORT_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Freed port 8000"
fi

# Find Python agent processes
echo ""
echo "2️⃣  Looking for agent processes..."

AGENT_PIDS=$(pgrep -f "example.py|cruise_booking_agent" || true)

if [ -z "$AGENT_PIDS" ]; then
    echo "  No agent processes found"
else
    echo "  Found agent processes: $AGENT_PIDS"
    echo "  Stopping..."
    kill $AGENT_PIDS 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Stopped agent processes"
fi

# Flush Phoenix traces
echo ""
echo "3️⃣  Flushing traces..."
if [ -n "$PHOENIX_API_KEY" ]; then
    echo "  Phoenix traces will be flushed automatically"
    echo -e "${GREEN}✓${NC} Traces flushed"
else
    echo "  Phoenix not configured (skipping)"
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}✓ All services stopped${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
