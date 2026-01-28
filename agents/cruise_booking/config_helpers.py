"""Helper functions for configuring models in notebooks and other contexts."""

import os
from typing import Optional, Dict, Any


def get_azure_config_for_phoenix() -> Dict[str, Any]:
    """
    Get Azure OpenAI configuration for use with Phoenix's OpenAIModel.
    
    Returns a dictionary with Azure configuration that can be passed to Phoenix's
    OpenAIModel or other evaluation models.
    
    Returns:
        Dictionary with Azure configuration keys, or empty dict if not configured
    """
    azure_config = {}
    
    azure_api_base = os.getenv('AZURE_API_BASE') or os.getenv('AZURE_OPENAI_API_BASE')
    azure_api_key = os.getenv('AZURE_API_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
    azure_api_version = os.getenv('AZURE_API_VERSION', '2024-02-15-preview')
    
    if azure_api_base and azure_api_key:
        azure_config = {
            'api_key': azure_api_key,
            'api_base': azure_api_base,
            'api_version': azure_api_version,
        }
    
    return azure_config


def configure_phoenix_model_for_azure(model_name: str) -> Dict[str, Any]:
    """
    Configure Phoenix OpenAIModel to use Azure OpenAI if Azure is configured.
    
    Args:
        model_name: Model name (e.g., "gpt-4.1-mini" or "gpt-4")
        
    Returns:
        Dictionary with configuration to pass to Phoenix's OpenAIModel
    """
    azure_config = get_azure_config_for_phoenix()
    
    if azure_config:
        # If Azure is configured, use Azure OpenAI
        # Phoenix's OpenAIModel can accept api_key, api_base, api_version
        return {
            'model': model_name,
            **azure_config
        }
    else:
        # Fall back to standard OpenAI
        return {
            'model': model_name
        }
