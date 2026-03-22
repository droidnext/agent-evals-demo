"""Configuration for cruise booking agents."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# LLM Configuration - Using LiteLLM native configuration
# LiteLLM automatically detects provider from model name and uses standard env vars:
# - OPENAI_API_KEY for OpenAI models (gpt-*)
# - AZURE_API_KEY for Azure OpenAI models (azure/*)
# - ANTHROPIC_API_KEY for Anthropic models (claude-*)
# - OPENROUTER_API_KEY for OpenRouter models (openrouter/*)
# - GOOGLE_API_KEY for Google models (gemini-*)
LLM_MODEL = os.getenv('LLM_MODEL', 'openrouter/google/gemini-2.5-flash')
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '2048'))

# Model configuration
MODEL_CONFIG = {
    'temperature': LLM_TEMPERATURE,
    'max_tokens': LLM_MAX_TOKENS,
}

# Phoenix configuration (optional)
PHOENIX_API_KEY = os.getenv('PHOENIX_API_KEY')
PHOENIX_PROJECT_NAME = os.getenv('PHOENIX_PROJECT_NAME', 'cruise-booking-agent')
PHOENIX_COLLECTOR_ENDPOINT = os.getenv('PHOENIX_COLLECTOR_ENDPOINT', 'https://app.phoenix.arize.com')

# Enable Phoenix if:
# 1. Using local Phoenix (localhost) - no API key needed
# 2. Using cloud Phoenix with API key
is_local_phoenix = 'localhost' in PHOENIX_COLLECTOR_ENDPOINT or '127.0.0.1' in PHOENIX_COLLECTOR_ENDPOINT
PHOENIX_ENABLED = is_local_phoenix or bool(PHOENIX_API_KEY)

# Local trace file export (writes spans to .traces_local/ as JSONL)
LOCAL_TRACE_ENABLED = os.getenv('LOCAL_TRACE_ENABLED', 'false').lower() == 'true'
LOCAL_TRACE_DIR = os.getenv('LOCAL_TRACE_DIR', str(project_root / '.traces_local'))


def get_model_instance(model: str = None):
    """
    Get the configured model instance using LiteLLM.
    
    Always returns a LiteLlm instance that can route to any provider.
    LiteLLM automatically detects the provider from the model name and uses
    standard environment variables:
    - OPENAI_API_KEY for OpenAI models (gpt-*)
    - AZURE_API_KEY for Azure OpenAI models (azure/*)
    - ANTHROPIC_API_KEY for Anthropic models (claude-*)
    - OPENROUTER_API_KEY for OpenRouter models (openrouter/*)
    - GOOGLE_API_KEY for Google models (gemini-*)
    
    Args:
        model: Model name to use. If None, uses LLM_MODEL from environment
    
    Returns:
        LiteLlm instance configured with the specified model
    
    Examples:
        # Use default model from LLM_MODEL
        model = get_model_instance()
        
        # Use specific model (LiteLLM auto-detects provider)
        model = get_model_instance('openrouter/google/gemini-2.0-flash-exp')
        model = get_model_instance('gpt-4o-mini')
        model = get_model_instance('azure/gpt-4')
        model = get_model_instance('claude-3-5-haiku-20241022')
        model = get_model_instance('gemini-2.0-flash-exp')
    """
    try:
        from google.adk.models.lite_llm import LiteLlm
        import litellm
        
        # Setup LiteLLM debug logging if enabled
        _setup_litellm_debug()
        
        # Use provided model or default from environment
        model_name = model if model is not None else LLM_MODEL
        
        # Configure LiteLLM to use standard environment variables
        # LiteLLM automatically reads from OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
        # based on the model name
        
        # Build kwargs for LiteLlm
        kwargs = {
            'model': model_name,
            'max_tokens': MODEL_CONFIG['max_tokens'],
            'temperature': MODEL_CONFIG['temperature'],
        }
        
        # For OpenRouter models, set the API base URL if specified
        # LiteLLM will use OPENROUTER_API_BASE from environment if available
        if model_name.startswith('openrouter/'):
            openrouter_base = os.getenv('OPENROUTER_API_BASE')
            if openrouter_base:
                # Set it in litellm config for this provider
                litellm.api_base = openrouter_base
        
        # For Azure OpenAI models, configure Azure-specific settings
        # Also handle models that might be Azure deployments (like gpt-4.1-mini)
        is_azure_model = (
            model_name.startswith('azure/') or 
            'gpt-4.1-mini' in model_name or
            os.getenv('AZURE_API_BASE') or 
            os.getenv('AZURE_OPENAI_API_BASE')
        )
        
        if is_azure_model:
            azure_api_base = os.getenv('AZURE_API_BASE') or os.getenv('AZURE_OPENAI_API_BASE')
            azure_api_version = os.getenv('AZURE_API_VERSION', '2024-02-15-preview')
            
            if azure_api_base:
                # Configure Azure OpenAI endpoint
                # LiteLLM will use AZURE_API_KEY from environment automatically
                kwargs['api_base'] = azure_api_base
                kwargs['api_version'] = azure_api_version
                
                # Note: Azure OpenAI content filtering severity is configured at the Azure
                # resource level, not via API parameters. If you're experiencing content
                # filtering issues:
                # 1. Check your Azure OpenAI resource content filter settings in Azure Portal
                # 2. Consider using a different deployment with less strict filtering
                # 3. Review and adjust prompts that might trigger content filters
        
        # LiteLLM will automatically use the appropriate API key from environment
        # based on the model name:
        # - openrouter/* models → OPENROUTER_API_KEY
        # - gpt-* models → OPENAI_API_KEY
        # - azure/* models → AZURE_API_KEY or AZURE_OPENAI_API_KEY
        # - claude-* models → ANTHROPIC_API_KEY
        # - gemini-* models → GOOGLE_API_KEY
        
        return LiteLlm(**kwargs)
        
    except ImportError as e:
        raise ImportError(
            f"LiteLlm not available. Install with: uv pip install litellm\nError: {e}"
        )


def get_model_name() -> str:
    """Get the configured LLM model name."""
    return LLM_MODEL


def get_model_config() -> dict:
    """Get the full model configuration."""
    return MODEL_CONFIG.copy()


def _setup_litellm_debug():
    """Setup LiteLLM debug logging based on environment variables.
    
    LiteLLM supports debug logging via:
    - LITELLM_LOG environment variable (INFO, DEBUG)
    - litellm.set_verbose = True for verbose logging
    - litellm._turn_on_debug() for detailed debug (logs API keys - use with caution)
    """
    import litellm
    
    # Check if LiteLLM debug logging is enabled via environment variable
    # LiteLLM automatically reads LITELLM_LOG from environment
    litellm_log_level = os.getenv("LITELLM_LOG", "").upper()
    
    if litellm_log_level:
        # Enable verbose logging
        litellm.set_verbose = True
        
        # For detailed debug mode (logs API keys - use with caution)
        if litellm_log_level == "DEBUG" and os.getenv("LITELLM_DETAILED_DEBUG", "false").lower() == "true":
            litellm._turn_on_debug()
    
    # Enable JSON logs if requested
    if os.getenv("LITELLM_JSON_LOGS", "false").lower() == "true":
        litellm.json_logs = True
