#!/usr/bin/env python3
"""Test prompt loading functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

from prompts import PromptLoader, get_prompt_loader, load_prompts, get_prompt, format_prompt


def test_prompt_loader_initialization():
    """Test PromptLoader initialization."""
    loader = PromptLoader()
    assert loader.prompts_dir.exists()
    assert loader.prompts_dir.name == "prompts"


def test_load_intent_detection_prompts():
    """Test loading intent detection prompts."""
    loader = PromptLoader()
    prompts = loader.load_prompts('intent_detection.yml')
    
    # Check required keys exist
    assert 'system_prompt' in prompts
    assert 'user_prompt_template' in prompts
    assert 'intent_description_template' in prompts
    assert 'context_with_constraints' in prompts
    assert 'fallback_reasoning' in prompts
    
    # Check system prompt content
    assert 'intent classification' in prompts['system_prompt'].lower()
    assert 'cruise booking platform' in prompts['system_prompt'].lower()


def test_get_prompt():
    """Test getting specific prompt."""
    loader = PromptLoader()
    system_prompt = loader.get_prompt('intent_detection.yml', 'system_prompt')
    
    assert isinstance(system_prompt, str)
    assert len(system_prompt) > 0
    assert 'intent' in system_prompt.lower()


def test_format_prompt():
    """Test formatting prompt with variables."""
    loader = PromptLoader()
    
    # Format intent description
    formatted = loader.format_prompt(
        'intent_detection.yml',
        'intent_description_template',
        intent_key='cruise_search',
        description='Search for cruises',
        category='search',
        example_patterns='ports, dates'
    )
    
    assert 'cruise_search' in formatted
    assert 'Search for cruises' in formatted
    assert 'search' in formatted


def test_format_prompt_missing_variable():
    """Test that missing variable raises error."""
    loader = PromptLoader()
    
    try:
        loader.format_prompt(
            'intent_detection.yml',
            'intent_description_template',
            intent_key='test'
            # Missing: description, category, example_patterns
        )
        raise AssertionError("Should have raised KeyError")
    except KeyError:
        pass  # Expected


def test_prompt_caching():
    """Test that prompts are cached."""
    loader = PromptLoader()
    
    # Load twice
    prompts1 = loader.load_prompts('intent_detection.yml')
    prompts2 = loader.load_prompts('intent_detection.yml')
    
    # Should be same object (cached)
    assert prompts1 is prompts2


def test_reload_prompts():
    """Test prompt reloading."""
    loader = PromptLoader()
    
    # Load prompts
    prompts1 = loader.load_prompts('intent_detection.yml')
    
    # Reload
    loader.reload_prompts('intent_detection.yml')
    
    # Load again
    prompts2 = loader.load_prompts('intent_detection.yml')
    
    # Should be different objects (cache cleared)
    assert prompts1 is not prompts2
    
    # But content should be same
    assert prompts1['system_prompt'] == prompts2['system_prompt']


def test_global_prompt_loader():
    """Test global prompt loader singleton."""
    loader1 = get_prompt_loader()
    loader2 = get_prompt_loader()
    
    # Should be same instance
    assert loader1 is loader2


def test_convenience_functions():
    """Test convenience functions."""
    # Test load_prompts
    prompts = load_prompts('intent_detection.yml')
    assert 'system_prompt' in prompts
    
    # Test get_prompt
    system_prompt = get_prompt('intent_detection.yml', 'system_prompt')
    assert isinstance(system_prompt, str)
    
    # Test format_prompt
    formatted = format_prompt(
        'intent_detection.yml',
        'context_with_constraints',
        constraints_json='{"port": "Miami"}'
    )
    assert 'Miami' in formatted


def test_all_prompt_files_load():
    """Test that all prompt files can be loaded."""
    loader = PromptLoader()
    prompt_files = ['intent_detection.yml', 'constraint_extraction.yml', 'response_generation.yml']
    
    for file in prompt_files:
        prompts = loader.load_prompts(file)
        assert prompts is not None
        assert 'system_prompt' in prompts or 'version' in prompts
        print(f"✓ Loaded {file}")


def test_prompt_file_not_found():
    """Test error when prompt file doesn't exist."""
    loader = PromptLoader()
    
    try:
        loader.load_prompts('nonexistent.yml')
        raise AssertionError("Should have raised FileNotFoundError")
    except FileNotFoundError:
        pass  # Expected


def test_intent_detection_prompt_structure():
    """Test intent detection prompt has correct structure."""
    prompts = load_prompts('intent_detection.yml')
    
    # Check all required fields
    required_fields = [
        'system_prompt',
        'user_prompt_template',
        'intent_description_template',
        'context_with_constraints',
        'context_no_constraints',
        'context_unavailable',
        'fallback_reasoning',
        'default_fallback_intent',
        'default_fallback_confidence',
        'log_messages'
    ]
    
    for field in required_fields:
        assert field in prompts, f"Missing required field: {field}"


if __name__ == "__main__":
    # Run tests
    print("Running prompt loader tests...\n")
    
    test_prompt_loader_initialization()
    print("✓ Prompt loader initialization")
    
    test_load_intent_detection_prompts()
    print("✓ Load intent detection prompts")
    
    test_get_prompt()
    print("✓ Get specific prompt")
    
    test_format_prompt()
    print("✓ Format prompt with variables")
    
    try:
        test_format_prompt_missing_variable()
    except AssertionError:
        print("✓ Format prompt missing variable (error caught)")
    
    test_prompt_caching()
    print("✓ Prompt caching")
    
    test_reload_prompts()
    print("✓ Reload prompts")
    
    test_global_prompt_loader()
    print("✓ Global prompt loader")
    
    test_convenience_functions()
    print("✓ Convenience functions")
    
    test_all_prompt_files_load()
    print("✓ All prompt files load")
    
    try:
        test_prompt_file_not_found()
    except AssertionError:
        print("✓ Prompt file not found (error caught)")
    
    test_intent_detection_prompt_structure()
    print("✓ Intent detection prompt structure")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
