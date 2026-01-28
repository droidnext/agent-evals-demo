#!/bin/bash
# Script to start Google ADK services for the cruise booking agent

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Starting ADK Services${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo "  Please create .env from env.example:"
    echo "  cp env.example .env"
    exit 1
fi

# Load environment variables (ignore comments and empty lines)
while IFS='=' read -r key value; do
    # Skip empty lines and comments
    if [[ -z "$key" ]] || [[ "$key" =~ ^#.* ]]; then
        continue
    fi
    # Remove inline comments
    value=$(echo "$value" | sed 's/#.*$//' | xargs)
    export "$key=$value"
done < .env

# Check for required environment variables
if [ -z "$LLM_MODEL" ]; then
    echo -e "${RED}✗ Error: LLM_MODEL not set in .env${NC}"
    exit 1
fi

# Check for API keys based on model name (LiteLLM auto-detects provider)
if [[ "$LLM_MODEL" == openrouter/* ]]; then
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${RED}✗ Error: OPENROUTER_API_KEY not set in .env (required for OpenRouter models)${NC}"
        exit 1
    fi
elif [[ "$LLM_MODEL" == azure/* ]]; then
    if [ -z "$AZURE_API_KEY" ] && [ -z "$AZURE_OPENAI_API_KEY" ]; then
        echo -e "${RED}✗ Error: AZURE_API_KEY or AZURE_OPENAI_API_KEY not set in .env (required for Azure OpenAI models)${NC}"
        exit 1
    fi
    if [ -z "$AZURE_API_BASE" ] && [ -z "$AZURE_OPENAI_API_BASE" ]; then
        echo -e "${RED}✗ Error: AZURE_API_BASE or AZURE_OPENAI_API_BASE not set in .env (required for Azure OpenAI models)${NC}"
        exit 1
    fi
elif [[ "$LLM_MODEL" == gpt-* ]]; then
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}✗ Error: OPENAI_API_KEY not set in .env (required for OpenAI models)${NC}"
        exit 1
    fi
elif [[ "$LLM_MODEL" == claude-* ]]; then
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${RED}✗ Error: ANTHROPIC_API_KEY not set in .env (required for Anthropic models)${NC}"
        exit 1
    fi
elif [[ "$LLM_MODEL" == gemini-* ]]; then
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo -e "${RED}✗ Error: GOOGLE_API_KEY not set in .env (required for Google models)${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Environment loaded"

# Check if Python environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}⚠️  Warning: No virtual environment detected${NC}"
    echo "  Consider activating a virtual environment first"
fi

# Check if dependencies are installed
echo ""
echo "1️⃣  Checking dependencies..."
python3 -c "import google.adk" 2>/dev/null || {
    echo -e "${RED}✗ Error: google-adk not installed${NC}"
    echo "  Install with: pip install -r requirements.txt"
    exit 1
}
echo -e "${GREEN}✓${NC} Dependencies installed"

# Load data if needed
echo ""
echo "2️⃣  Checking data..."
if [ ! -f "data/cruises.jsonl" ]; then
    echo -e "${RED}⚠️  Warning: data/cruises.jsonl not found${NC}"
    echo "  Run: python scripts/load_data.py"
else
    echo -e "${GREEN}✓${NC} Data files present"
fi

# Start Phoenix tracing (if configured)
echo ""
echo "3️⃣  Checking observability..."
if [ -n "$PHOENIX_API_KEY" ]; then
    echo -e "${GREEN}✓${NC} Phoenix tracing enabled"
    echo "  Dashboard: https://app.phoenix.arize.com"
else
    echo "  Phoenix tracing not configured (optional)"
fi

# Start ADK development server
echo ""
echo "4️⃣  Starting ADK development server..."
echo -e "${BLUE}================================${NC}"
echo ""

# Start ADK web server
if command -v adk &> /dev/null; then
    echo "Starting ADK Web UI..."
    echo ""
    echo "Access the UI at: ${GREEN}http://127.0.0.1:8000${NC}"
    echo ""
    adk web agents/ --port 8000 --reload
else
    echo "ADK CLI not found. Running Python example instead..."
    python3 example.py
fi
