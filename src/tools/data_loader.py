"""Data loading utilities for cruise data - focuses on loading and injecting data."""

import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """Loads and injects cruise data into various systems.
    
    This class focuses on:
    - Loading data from files (JSONL, Parquet, CSV)
    - Injecting data into vector stores
    - Validating data quality
    - Data transformation and preparation
    
    For searching data, use DataSearch instead.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cruises: List[Dict[str, Any]] = []
        self.pricing_df: Optional[pd.DataFrame] = None
    
    def load_jsonl(self, filename: str = "cruises.jsonl") -> List[Dict[str, Any]]:
        """Load data from a JSON Lines file."""
        filepath = self.data_dir / filename
        cruises = []
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}. Using empty dataset.")
            return cruises
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        cruises.append(json.loads(line))
            
            self.cruises = cruises
            logger.info(f"Loaded {len(cruises)} cruises from {filename}")
            return cruises
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
    
    def load_parquet(self, filename: str = "cruises.parquet") -> pd.DataFrame:
        """Load data from a Parquet file."""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}. Using empty DataFrame.")
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(filepath)
            self.pricing_df = df
            logger.info(f"Loaded {len(df)} rows from {filename}")
            return df
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return pd.DataFrame()
    
    def inject_to_vector_store(self, vector_store, batch_size: int = 100) -> int:
        """Inject loaded cruise data into a vector store.
        
        Args:
            vector_store: Vector store instance (e.g., ChromaDB)
            batch_size: Number of documents to inject per batch
            
        Returns:
            Number of documents injected
        """
        if not self.cruises:
            logger.warning("No cruise data loaded to inject")
            return 0
        
        try:
            count = 0
            for i in range(0, len(self.cruises), batch_size):
                batch = self.cruises[i:i + batch_size]
                # Convert to format suitable for vector store
                documents = [json.dumps(cruise) for cruise in batch]
                # Use cruise_id if available, otherwise use fallback
                ids = [cruise.get("cruise_id", cruise.get("id", f"cruise_{i+j}")) 
                       for j, cruise in enumerate(batch)]
                
                vector_store.add_documents(documents=documents, ids=ids)
                count += len(batch)
                logger.debug(f"Injected batch {i//batch_size + 1}: {len(batch)} documents")
            
            logger.info(f"Successfully injected {count} documents to vector store")
            return count
        except Exception as e:
            logger.error(f"Error injecting to vector store: {e}")
            return 0
    
    def validate_data(self) -> Dict[str, Any]:
        """Validate loaded data quality.
        
        Returns:
            Validation report with errors and warnings
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        # Check cruise data
        if not self.cruises:
            report["warnings"].append("No cruise data loaded")
        else:
            report["stats"]["cruise_count"] = len(self.cruises)
            
            # Check for required fields (flexible field names)
            required_fields = [
                ("cruise_id", "id"),  # cruise_id or id
                ("ship_name", "name"),  # ship_name or name
                "departure_port"
            ]
            for i, cruise in enumerate(self.cruises[:10]):  # Sample first 10
                for field in required_fields:
                    if isinstance(field, tuple):
                        # Check if any of the alternative field names exist
                        if not any(f in cruise for f in field):
                            report["errors"].append(f"Cruise {i}: Missing required field '{field[0]}' or '{field[1]}'")
                            report["valid"] = False
                    else:
                        if field not in cruise:
                            report["errors"].append(f"Cruise {i}: Missing required field '{field}'")
                            report["valid"] = False
        
        # Check pricing data
        if self.pricing_df is not None and not self.pricing_df.empty:
            report["stats"]["pricing_rows"] = len(self.pricing_df)
        else:
            report["warnings"].append("No pricing data loaded")
        
        return report
    
    def get_loaded_data(self) -> Dict[str, Any]:
        """Get currently loaded data.
        
        Returns:
            Dictionary with cruises and pricing data
        """
        return {
            "cruises": self.cruises,
            "pricing_df": self.pricing_df,
            "stats": {
                "cruise_count": len(self.cruises),
                "pricing_rows": len(self.pricing_df) if self.pricing_df is not None else 0
            }
        }
