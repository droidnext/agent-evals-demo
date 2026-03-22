"""
LLM-As-Judge Evaluation Prompts

This module contains YAML prompt templates for evaluating agent responses
using LLM-as-judge methodology.

All prompts are stored as YAML files and can be loaded dynamically.
"""

import os
import yaml
from pathlib import Path

# Get the directory containing this file
PROMPTS_DIR = Path(__file__).parent


def load_prompt(prompt_name: str) -> dict:
    """
    Load a prompt template from a YAML file.
    
    Args:
        prompt_name: Name of the prompt file (without .yaml extension)
                    e.g., 'response_relevance', 'response_completeness'
    
    Returns:
        Dictionary containing the prompt configuration including:
        - name: Evaluator name
        - criterion_id: Numeric ID
        - criterion_name: Human-readable name
        - weight: Weight in overall score (0-1)
        - score_range: [min, max] score values
        - type: 'llm_as_judge'
        - description: Brief description
        - template: Prompt template string
        - required_variables: List of required template variables
        - optional_variables: List of optional template variables
    
    Example:
        >>> prompt = load_prompt('response_relevance')
        >>> template = prompt['template']
        >>> formatted = template.format(input="...", output="...", expected_response_type="...")
    """
    prompt_file = PROMPTS_DIR / f"{prompt_name}.yaml"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r') as f:
        return yaml.safe_load(f)


def load_all_prompts() -> dict:
    """
    Load all available prompt templates.
    
    Returns:
        Dictionary mapping prompt names to their configurations
    
    Example:
        >>> prompts = load_all_prompts()
        >>> relevance_template = prompts['response_relevance']['template']
    """
    prompt_files = [
        'response_relevance',
        'response_completeness',
        'response_coherence',
        'query_understanding',
        'instruction_following',
        'semantic_search_quality'
    ]
    
    return {name: load_prompt(name) for name in prompt_files}


def get_template(prompt_name: str) -> str:
    """
    Get just the template string from a prompt.
    
    Args:
        prompt_name: Name of the prompt file (without .yaml extension)
    
    Returns:
        Template string ready for formatting
    
    Example:
        >>> template = get_template('response_relevance')
        >>> formatted = template.format(input="...", output="...", expected_response_type="...")
    """
    prompt = load_prompt(prompt_name)
    return prompt['template']


# Pre-load all templates for convenient access
RESPONSE_RELEVANCE = load_prompt('response_relevance')
RESPONSE_COMPLETENESS = load_prompt('response_completeness')
RESPONSE_COHERENCE = load_prompt('response_coherence')
QUERY_UNDERSTANDING = load_prompt('query_understanding')
INSTRUCTION_FOLLOWING = load_prompt('instruction_following')
SEMANTIC_SEARCH_QUALITY = load_prompt('semantic_search_quality')

# Also provide template strings directly for backward compatibility
RESPONSE_RELEVANCE_TEMPLATE = RESPONSE_RELEVANCE['template']
RESPONSE_COMPLETENESS_TEMPLATE = RESPONSE_COMPLETENESS['template']
RESPONSE_COHERENCE_TEMPLATE = RESPONSE_COHERENCE['template']
QUERY_UNDERSTANDING_TEMPLATE = QUERY_UNDERSTANDING['template']
INSTRUCTION_FOLLOWING_TEMPLATE = INSTRUCTION_FOLLOWING['template']
SEMANTIC_SEARCH_QUALITY_TEMPLATE = SEMANTIC_SEARCH_QUALITY['template']

__all__ = [
    # Functions
    'load_prompt',
    'load_all_prompts',
    'get_template',
    
    # Full prompt configs
    'RESPONSE_RELEVANCE',
    'RESPONSE_COMPLETENESS',
    'RESPONSE_COHERENCE',
    'QUERY_UNDERSTANDING',
    'INSTRUCTION_FOLLOWING',
    'SEMANTIC_SEARCH_QUALITY',
    
    # Template strings (for backward compatibility)
    'RESPONSE_RELEVANCE_TEMPLATE',
    'RESPONSE_COMPLETENESS_TEMPLATE',
    'RESPONSE_COHERENCE_TEMPLATE',
    'QUERY_UNDERSTANDING_TEMPLATE',
    'INSTRUCTION_FOLLOWING_TEMPLATE',
    'SEMANTIC_SEARCH_QUALITY_TEMPLATE',
]
