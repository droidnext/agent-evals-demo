"""Prompt management utilities."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Simple logger for prompt loading
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PromptLoader:
    """Loads and manages prompts from YAML files."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt YAML files
        """
        if prompts_dir is None:
            # Default to prompts directory at project root
            prompts_dir = Path(__file__).parent
        
        self.prompts_dir = Path(prompts_dir)
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Prompt loader initialized: {self.prompts_dir}")
    
    def load_prompts(self, prompt_file: str) -> Dict[str, Any]:
        """
        Load prompts from a YAML file.
        
        Args:
            prompt_file: Name of the prompt file (e.g., 'intent_detection.yml')
            
        Returns:
            Dictionary containing prompts and templates
        """
        # Check cache first
        if prompt_file in self._prompt_cache:
            logger.debug(f"Prompt cache hit: {prompt_file}")
            return self._prompt_cache[prompt_file]
        
        # Load from file
        file_path = self.prompts_dir / prompt_file
        
        if not file_path.exists():
            logger.error(f"Prompt file not found: {file_path}")
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                prompts = yaml.safe_load(f)
            
            # Cache the prompts
            self._prompt_cache[prompt_file] = prompts
            
            logger.info(f"Prompts loaded from {prompt_file}: {list(prompts.keys())}")
            return prompts
            
        except Exception as e:
            logger.error(f"Error loading prompts from {prompt_file}: {e}")
            raise
    
    def get_prompt(self, prompt_file: str, prompt_key: str) -> str:
        """
        Get a specific prompt from a file.
        
        Args:
            prompt_file: Name of the prompt file
            prompt_key: Key of the prompt to retrieve
            
        Returns:
            Prompt string
        """
        prompts = self.load_prompts(prompt_file)
        
        if prompt_key not in prompts:
            logger.error(f"Prompt key '{prompt_key}' not found in {prompt_file}")
            raise KeyError(f"Prompt key '{prompt_key}' not found in {prompt_file}")
        
        return prompts[prompt_key]
    
    def format_prompt(
        self,
        prompt_file: str,
        prompt_key: str,
        **kwargs
    ) -> str:
        """
        Get and format a prompt with variables.
        
        Args:
            prompt_file: Name of the prompt file
            prompt_key: Key of the prompt to retrieve
            **kwargs: Variables to format the prompt with
            
        Returns:
            Formatted prompt string
        """
        template = self.get_prompt(prompt_file, prompt_key)
        
        try:
            formatted = template.format(**kwargs)
            logger.debug(f"Formatted prompt {prompt_key} from {prompt_file} with vars: {list(kwargs.keys())}")
            return formatted
        except KeyError as e:
            logger.error(f"Error formatting prompt {prompt_key} from {prompt_file}: missing variable {e}")
            raise
    
    def reload_prompts(self, prompt_file: Optional[str] = None):
        """
        Reload prompts from disk (useful for development).
        
        Args:
            prompt_file: Specific file to reload, or None to reload all
        """
        if prompt_file:
            if prompt_file in self._prompt_cache:
                del self._prompt_cache[prompt_file]
                logger.info(f"Prompt cache cleared for: {prompt_file}")
        else:
            self._prompt_cache.clear()
            logger.info("All prompt cache cleared")


# Global prompt loader instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader(prompts_dir: Optional[Path] = None) -> PromptLoader:
    """
    Get the global prompt loader instance.
    
    Args:
        prompts_dir: Directory containing prompt YAML files
        
    Returns:
        PromptLoader instance
    """
    global _prompt_loader
    
    if _prompt_loader is None:
        _prompt_loader = PromptLoader(prompts_dir)
    
    return _prompt_loader


def load_prompts(prompt_file: str) -> Dict[str, Any]:
    """
    Convenience function to load prompts.
    
    Args:
        prompt_file: Name of the prompt file
        
    Returns:
        Dictionary containing prompts
    """
    return get_prompt_loader().load_prompts(prompt_file)


def get_prompt(prompt_file: str, prompt_key: str) -> str:
    """
    Convenience function to get a specific prompt.
    
    Args:
        prompt_file: Name of the prompt file
        prompt_key: Key of the prompt
        
    Returns:
        Prompt string
    """
    return get_prompt_loader().get_prompt(prompt_file, prompt_key)


def format_prompt(prompt_file: str, prompt_key: str, **kwargs) -> str:
    """
    Convenience function to format a prompt.
    
    Args:
        prompt_file: Name of the prompt file
        prompt_key: Key of the prompt
        **kwargs: Variables to format with
        
    Returns:
        Formatted prompt string
    """
    return get_prompt_loader().format_prompt(prompt_file, prompt_key, **kwargs)
