# Cruise Booking Agent - Configuration

## Model Configuration

All agents (root and sub-agents) use the model specified in your `.env` file:

```bash
# .env
LLM_MODEL=google/gemini-2.5-flash
```

### Supported Models (LiteLLM Native)

LiteLLM automatically detects the provider from the model name. No need to set `LLM_PROVIDER`!

#### OpenRouter (Recommended)
```bash
LLM_MODEL=openrouter/google/gemini-2.5-flash    # Fast, cost-effective
LLM_MODEL=openrouter/google/gemini-2.0-flash-exp # Experimental
LLM_MODEL=openrouter/anthropic/claude-3.5-sonnet # High quality
# Requires: OPENROUTER_API_KEY
```

#### OpenAI
```bash
LLM_MODEL=gpt-4o                     # Latest GPT-4
LLM_MODEL=gpt-4o-mini                # Cost-effective
# Requires: OPENAI_API_KEY
```

#### Azure OpenAI
```bash
LLM_MODEL=azure/gpt-4                # GPT-4 via Azure
LLM_MODEL=azure/gpt-35-turbo        # GPT-3.5 Turbo via Azure
LLM_MODEL=azure/gpt-4o              # GPT-4o via Azure
# Requires: AZURE_API_KEY, AZURE_API_BASE
# Optional: AZURE_API_VERSION (defaults to latest)
```

#### Anthropic
```bash
LLM_MODEL=claude-3-5-sonnet-20241022 # Latest Claude
LLM_MODEL=claude-3-5-haiku-20241022  # Faster, cheaper
# Requires: ANTHROPIC_API_KEY
```

#### Google
```bash
LLM_MODEL=gemini-2.0-flash-exp        # Experimental
LLM_MODEL=gemini-pro                  # Stable
# Requires: GOOGLE_API_KEY
```

## How It Works

The `config.py` module loads the model from environment variables:

```python
# agents/cruise_booking/config.py
import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')

def get_model_name() -> str:
    """Get the configured LLM model name."""
    return LLM_MODEL
```

All agents import and use this configuration:

```python
# agent.py, sub_agents/*.py
from .config import get_model_name

MODEL_NAME = get_model_name()

agent = Agent(
    model=MODEL_NAME,  # Uses value from .env
    name='AgentName',
    instruction="...",
    tools=[...]
)
```

## Changing Models

To change the model for all agents:

1. **Edit `.env` file**:
   ```bash
   LLM_MODEL=anthropic/claude-3.5-sonnet
   ```

2. **Restart ADK server**:
   ```bash
   ./scripts/start_adk.sh
   ```

All agents will now use the new model!

## Model Configuration Options

You can also configure:

```bash
# .env
LLM_TEMPERATURE=0.7    # Creativity (0.0 - 1.0)
LLM_MAX_TOKENS=4096    # Max response length
```

Access via:
```python
from agents.cruise_booking.config import get_model_config

config = get_model_config()
# {'model': 'google/gemini-2.5-flash', 'temperature': 0.7, 'max_tokens': 4096}
```

## Per-Agent Model Override (Advanced)

If you need different models for specific agents, you can override:

```python
# sub_agents/special_agent.py
from google.adk.agents.llm_agent import Agent

# Override with specific model
special_agent = Agent(
    model='gpt-4o',  # Different from default
    name='SpecialAgent',
    instruction="...",
    tools=[...]
)
```

## Verification

Check which model is being used:

```python
from agents.cruise_booking.config import get_model_name

print(f"Using model: {get_model_name()}")
```

Or via shell:
```bash
grep "^LLM_MODEL=" .env
```

## Cost Optimization

Model recommendations by use case:

### Development/Testing
```bash
LLM_MODEL=google/gemini-2.5-flash  # Fast, cheap
```

### Production (Quality)
```bash
LLM_MODEL=anthropic/claude-3.5-sonnet  # High quality
```

### Production (Speed)
```bash
LLM_MODEL=google/gemini-2.5-flash  # Fast, reliable
```

### Production (Balanced)
```bash
LLM_MODEL=gpt-4o-mini  # Good quality, cost-effective
```

## Configuration File Structure

```
agents/cruise_booking/
├── config.py           # Central configuration
├── agent.py            # Root agent (uses config)
├── sub_agents/         # All sub-agents use config
│   ├── itinerary_agent.py
│   ├── pricing_agent.py
│   ├── search_agent.py
│   └── recommendation_agent.py
└── tools/              # Tools (model-agnostic)
```

## Environment Variables Reference

```bash
# Required
LLM_MODEL=openrouter/google/gemini-2.5-flash  # LiteLLM auto-detects provider
OPENROUTER_API_KEY=your_key_here  # For openrouter/* models

# Optional
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
OPENROUTER_API_BASE=https://openrouter.ai/api/v1  # Optional, uses default if not set

# Other API Keys (set based on model you want to use)
OPENAI_API_KEY=your_key_here      # For gpt-* models
AZURE_API_KEY=your_key_here       # For azure/* models
AZURE_API_BASE=https://your-resource-name.openai.azure.com  # Required for azure/* models
AZURE_API_VERSION=2024-02-15-preview  # Optional for azure/* models
ANTHROPIC_API_KEY=your_key_here   # For claude-* models
GOOGLE_API_KEY=your_key_here      # For gemini-* models

# Observability (Optional)
PHOENIX_API_KEY=your_phoenix_key
PHOENIX_PROJECT_NAME=cruise-booking-agent
```

## Troubleshooting

### Model not found
```
Error: Model 'xyz' not found
```
**Solution**: Check model name in `.env` matches provider's available models

### API key error
```
Error: Invalid API key
```
**Solution**: Verify `OPENROUTER_API_KEY` (or respective provider key) is set correctly

### Wrong model being used
```bash
# Check configuration is loaded
python -c "from agents.cruise_booking.config import get_model_name; print(get_model_name())"

# Should print: google/gemini-2.5-flash (or your configured model)
```

## Best Practices

1. ✅ **Use environment variables** - Never hardcode model names
2. ✅ **Set in .env** - Easy to change without code updates
3. ✅ **Test after changes** - Restart ADK after updating .env
4. ✅ **Document changes** - Note which models work best
5. ✅ **Monitor costs** - Track usage per model

---

**Configuration Module**: `agents/cruise_booking/config.py`  
**Model Source**: `.env` file  
**Default Fallback**: `gemini-2.0-flash-exp`
