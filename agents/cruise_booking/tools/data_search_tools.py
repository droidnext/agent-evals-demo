"""Data search tools for cruise booking agent."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.tools.data_search import DataSearch
from ..config import tracer
from ..prompt_loader import get_prompt_loader

# Initialize data search
_data_search = DataSearch()
_prompt_loader = get_prompt_loader()


def build_sql_generation_prompt(
    user_prompt: str,
    columns: List[str],
    table_name: str = "cruises",
) -> str:
    """
    Format the SQL generation prompt given a natural language request and schema,
    using the template loaded from prompts/sql_generation.yaml.
    """
    prompt_template = _prompt_loader.get_instruction("sql_generation")
    return prompt_template.format(
        prompt=user_prompt,
        columns=", ".join(columns),
        table_name=table_name,
    )


@tracer.tool
def search_cruises(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute a raw SQL query against the cruise data.
    
    Args:
        sql_query: DuckDB-compatible SQL query that references tables:
            - cruises: main cruise metadata with columns: cruise_id, ship_name, departure_port, 
              departure_date, duration (in days), destination, ports_of_call, cabin_type, 
              price_per_person, total_price, availability, amenities, description
            - pricing: pricing information with columns: cruise_id, starting_price (if available)
    
    Note: Use exact column names as listed above. The 'duration' column contains days (not 'duration_days').
    
    Returns:
        List of result rows as dictionaries.
    """
    return _data_search.execute_sql_query(sql_query)


@tracer.tool
def get_cruise_by_id(
    cruise_id: Optional[str] = None,
    cruise_ids: Optional[List[str]] = None,
) -> Any:
    """
    Get detailed information about one or more cruises.
    
    Args:
        cruise_id: Unique identifier for a single cruise.
        cruise_ids: List of cruise identifiers to fetch multiple cruises.
    
    Returns:
        - If cruise_ids is provided: list of cruise dictionaries (may be empty).
        - Else if cruise_id is provided: single cruise dictionary or None if not found.
    """
    # Multiple IDs take precedence if provided
    if cruise_ids:
        results: List[Dict[str, Any]] = []
        for cid in cruise_ids:
            cruise = _data_search.get_cruise_by_id(cid)
            if cruise:
                results.append(cruise)
        return results

    if cruise_id is not None:
        return _data_search.get_cruise_by_id(cruise_id)

    return None


@tracer.tool
def get_pricing_info(
    cruise_id: str,
    cabin_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get pricing information for a specific cruise.
    
    Args:
        cruise_id: Unique identifier for the cruise
        cabin_type: Type of cabin (e.g., 'interior', 'oceanview', 'balcony', 'suite')
    
    Returns:
        Dictionary with pricing details. Currently cabin_type is
        accepted for future compatibility but not used, because the
        underlying DataSearch.get_pricing method only supports
        cruise-level pricing.
    """
    # DataSearch.get_pricing currently only accepts cruise_id, so we must
    # not pass cabin_type here to avoid a positional argument error.
    return _data_search.get_pricing(cruise_id)


@tracer.tool
def search_by_price_range(
    min_price: float,
    max_price: float,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Find cruises within a specific price range.
    
    Args:
        min_price: Minimum price per person in USD
        max_price: Maximum price per person in USD
        limit: Maximum number of results to return
    
    Returns:
        List of cruises sorted by price.
    """
    return _data_search.search_by_price_range(min_price, max_price, limit)


@tracer.tool
def get_all_cruises(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all available cruises.
    
    Args:
        limit: Optional limit on number of results
    
    Returns:
        List of all cruise dictionaries.
    """
    return _data_search.get_all_cruises(limit)


@tracer.tool
def get_data_stats() -> Dict[str, Any]:
    """
    Get statistics about available cruise data.
    
    Returns:
        Dictionary with counts and summary statistics.
    """
    return _data_search.get_stats()
