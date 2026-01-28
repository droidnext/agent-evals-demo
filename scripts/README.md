# Scripts Directory

Essential utility scripts for the Cruise Booking Agent system.

**Total: 7 scripts** (simplified from 13)

---

## 🚀 Quick Start

```bash
# 1. Start Phoenix (observability)
./scripts/start_phoenix.sh

# 2. Load cruise data
python scripts/load_data.py

# 3. Start the agent
./scripts/start_adk.sh

# 4. Test it
python scripts/test_agent.py
```

---

## Phoenix Scripts (Docker)

### Start Phoenix
```bash
./scripts/start_phoenix.sh
```
Starts Phoenix Arize using Docker Compose from `phoenix-arize/docker-compose.yml`

**Access**: http://localhost:6006  
**Credentials**: admin@example.com / admin

### Stop Phoenix
```bash
./scripts/stop_phoenix.sh
```
Stops the Phoenix Docker container

### Other Phoenix Commands
```bash
# View logs
docker compose -f phoenix-arize/docker-compose.yml logs -f

# Check status
docker ps | grep phoenix

# Restart
docker compose -f phoenix-arize/docker-compose.yml restart
```

---

## Agent Scripts

### Start Agent
```bash
./scripts/start_adk.sh
```
Starts the ADK-based cruise booking agent

### Stop Agent
```bash
./scripts/stop_adk.sh
```
Stops the running agent

---

## Data Management

### Load Data
```bash
python scripts/load_data.py
```
- Loads cruise data from `data/cruises.jsonl`
- Injects into vector store (ChromaDB)
- **Run once** before first agent use

**To reload**: Just run again (will clear and reload)

---

## Testing & Verification

### Test Agent
```bash
python scripts/test_agent.py
```
Runs test queries against the agent and shows responses

### Verify Phoenix
```bash
python scripts/verify_phoenix.py
```
- Checks Phoenix connection
- Validates tracing configuration
- Sends test trace

---

## Complete Workflow

### First Time Setup
```bash
# 1. Start Phoenix
./scripts/start_phoenix.sh

# 2. Load data
python scripts/load_data.py

# 3. Start agent
./scripts/start_adk.sh

# 4. Test
python scripts/test_agent.py
```

### Daily Development
```bash
# Check Phoenix is running
docker ps | grep phoenix

# Test the agent
python scripts/test_agent.py
```

### Shutdown
```bash
# Stop agent
./scripts/stop_adk.sh

# Stop Phoenix (optional)
./scripts/stop_phoenix.sh
```

---

## Direct Docker Commands

All Phoenix commands can be run directly:

```bash
# Start
cd phoenix-arize && docker compose up -d

# Stop
cd phoenix-arize && docker compose down

# Logs
cd phoenix-arize && docker compose logs -f

# Status
docker ps -a | grep phoenix

# Restart
cd phoenix-arize && docker compose restart
```

---

## Environment Variables

Scripts use `.env` configuration:

```bash
# LLM Configuration
LLM_PROVIDER=openrouter
LLM_MODEL=openrouter/google/gemini-2.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# API Keys (set one based on your provider)
OPENROUTER_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

---

## Troubleshooting

### Phoenix won't start
```bash
# Check Docker
docker info

# Check logs
docker compose -f phoenix-arize/docker-compose.yml logs

# Reset
docker compose -f phoenix-arize/docker-compose.yml down -v
docker compose -f phoenix-arize/docker-compose.yml up -d
```

### Agent errors
```bash
# Verify Phoenix connection
python scripts/verify_phoenix.py

# Check environment
cat .env | grep LLM_

# Reload data
python scripts/load_data.py
```

---

## Files

```
scripts/
├── start_phoenix.sh      # Start Phoenix (Docker)
├── stop_phoenix.sh       # Stop Phoenix
├── start_adk.sh          # Start agent
├── stop_adk.sh           # Stop agent
├── load_data.py          # Load cruise data
├── test_agent.py         # Test agent queries
├── verify_phoenix.py     # Verify Phoenix setup
└── README.md             # This file
```

**Total**: 7 essential scripts (+ README)

---

**Last Updated**: January 20, 2026  
**Simplified**: Removed 5 redundant scripts  
**Status**: Production ready
