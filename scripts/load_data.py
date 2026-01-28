#!/usr/bin/env python3
"""
Script to load and inject cruise data into the system.

This script:
1. Loads data from JSONL and Parquet files
2. Validates data quality
3. Injects data into vector stores
4. Reports loading statistics

Usage:
    python scripts/load_data.py
    python scripts/load_data.py --data-dir ./data
    python scripts/load_data.py --validate-only
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from dotenv import load_dotenv

from src.tools.data_loader import DataLoader
from src.tools.vector_store import VectorStore
from src.utils.logging_config import get_logger

# Load environment
load_dotenv()

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Load cruise data into the system")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing data files (default: data)"
    )
    parser.add_argument(
        "--jsonl-file",
        default="cruises.jsonl",
        help="JSONL file name (default: cruises.jsonl)"
    )
    parser.add_argument(
        "--parquet-file",
        default="cruises.parquet",
        help="Parquet file name (default: cruises.parquet)"
    )
    parser.add_argument(
        "--inject-vector-store",
        action="store_true",
        help="Inject data into vector store"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate data without loading"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for vector store injection (default: 100)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("CRUISE DATA LOADER")
    print("=" * 80)
    print()
    
    # Initialize data loader
    print(f"📂 Data directory: {args.data_dir}")
    loader = DataLoader(data_dir=args.data_dir)
    
    # Load JSONL data
    print(f"\n1️⃣  Loading JSONL: {args.jsonl_file}")
    print("-" * 80)
    cruises = loader.load_jsonl(args.jsonl_file)
    print(f"✓ Loaded {len(cruises)} cruise records")
    
    # Load Parquet data
    print(f"\n2️⃣  Loading Parquet: {args.parquet_file}")
    print("-" * 80)
    pricing_df = loader.load_parquet(args.parquet_file)
    print(f"✓ Loaded {len(pricing_df) if pricing_df is not None else 0} pricing records")
    
    # Validate data
    print(f"\n3️⃣  Validating Data")
    print("-" * 80)
    validation = loader.validate_data()
    
    if validation["valid"]:
        print("✓ Data validation passed")
    else:
        print("✗ Data validation failed")
        for error in validation["errors"]:
            print(f"  ERROR: {error}")
    
    for warning in validation["warnings"]:
        print(f"  WARNING: {warning}")
    
    print("\nStatistics:")
    for key, value in validation["stats"].items():
        print(f"  {key}: {value}")
    
    if args.validate_only:
        print("\n✓ Validation complete (--validate-only mode)")
        return 0
    
    # Inject into vector store
    if args.inject_vector_store:
        print(f"\n4️⃣  Injecting into Vector Store")
        print("-" * 80)
        try:
            vector_store = VectorStore()
            injected = loader.inject_to_vector_store(vector_store, batch_size=args.batch_size)
            print(f"✓ Injected {injected} documents into vector store")
        except Exception as e:
            print(f"✗ Error injecting to vector store: {e}")
            return 1
    
    # Summary
    print("\n" + "=" * 80)
    print("✓ DATA LOADING COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  Cruise records: {len(cruises)}")
    print(f"  Pricing records: {len(pricing_df) if pricing_df is not None else 0}")
    if args.inject_vector_store:
        print(f"  Vector store docs: {injected}")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        sys.exit(1)
