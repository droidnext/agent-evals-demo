"""Utility to load agent prompts from YAML files."""

import os
from pathlib import Path
from typing import Dict, Any
import yaml


class PromptLoader:
    """Load and manage agent prompts from YAML files."""
    
    def __init__(self, prompts_dir: str = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Path to prompts directory. If None, uses project root/prompts
        """
        if prompts_dir is None:
            # Get project root (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent
            prompts_dir = project_root / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_prompt(self, filename: str) -> Dict[str, Any]:
        """
        Load a prompt from a YAML file.
        
        Args:
            filename: Name of the YAML file (with or without .yml/.yaml extension)
        
        Returns:
            Dictionary containing prompt configuration
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        # Check cache first
        if filename in self._cache:
            return self._cache[filename]
        
        # Add extension if not provided
        if not filename.endswith(('.yml', '.yaml')):
            filename = f"{filename}.yaml"
        
        prompt_path = self.prompts_dir / filename
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_data = yaml.safe_load(f)
        
        # Cache the loaded prompt
        self._cache[filename] = prompt_data
        
        return prompt_data
    
    def get_instruction(self, filename: str) -> str:
        """
        Get the instruction text from a prompt file.
        
        Args:
            filename: Name of the YAML file
        
        Returns:
            Instruction string
        """
        prompt_data = self.load_prompt(filename)
        return prompt_data.get('instruction', '')
    
    def get_name(self, filename: str) -> str:
        """
        Get the agent name from a prompt file.
        
        Args:
            filename: Name of the YAML file
        
        Returns:
            Agent name
        """
        prompt_data = self.load_prompt(filename)
        return prompt_data.get('name', '')
    
    def reload_prompt(self, filename: str) -> Dict[str, Any]:
        """
        Force reload a prompt file, bypassing cache.
        
        Args:
            filename: Name of the YAML file
        
        Returns:
            Dictionary containing prompt configuration
        """
        # Remove from cache if exists
        if filename in self._cache:
            del self._cache[filename]
        
        return self.load_prompt(filename)
    
    def clear_cache(self):
        """Clear all cached prompts."""
        self._cache.clear()


# Global prompt loader instance
_prompt_loader = None


def get_prompt_loader() -> PromptLoader:
    """Get or create the global prompt loader instance."""
    global _prompt_loader
    
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    
    return _prompt_loader


def load_agent_instruction(agent_name: str) -> str:
    """
    Convenience function to load an agent's instruction.
    
    Args:
        agent_name: Name of the agent (e.g., 'root_agent', 'itinerary_agent')
    
    Returns:
        Instruction string
    """
    loader = get_prompt_loader()
    return loader.get_instruction(agent_name)
