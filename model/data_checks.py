"""
Data validation and inference utilities for DroughtGuard training pipeline.
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional
import warnings


def load_and_validate_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load CSV data and perform basic validation.
    
    Args:
        data_path: Path to CSV file. If None, uses ENV TRAIN_DATA_PATH or default.
        
    Returns:
        Validated DataFrame
        
    Raises:
        ValueError: If critical validation checks fail
    """
    # Determine data path
    if data_path is None:
        data_path = os.getenv('TRAIN_DATA_PATH', 'data/features.csv')
    
    if not os.path.exists(data_path):
        raise ValueError(f"Data file not found: {data_path}")
    
    print(f"Loading data from: {data_path}")
    
    # Load data
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        raise ValueError(f"Failed to load CSV: {e}")
    
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    return df


def infer_columns(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[str, str]:
    """
    Infer id_col and date_col from DataFrame if not specified in config.
    
    Args:
        df: DataFrame to analyze
        config: Configuration dictionary
        
    Returns:
        Tuple of (id_col, date_col)
    """
    id_col = config.get('columns', {}).get('id_col')
    date_col = config.get('columns', {}).get('date_col')
    
    # Infer id_col if not specified
    if not id_col:
        # Look for common region/county column names
        region_candidates = ['region', 'county', 'area', 'location', 'id']
        for candidate in region_candidates:
            if candidate in df.columns:
                id_col = candidate
                break
        
        if not id_col:
            # Fallback: use first non-numeric column that looks like an ID
            for col in df.columns:
                if df[col].dtype == 'object' and df[col].nunique() < len(df) * 0.5:
                    id_col = col
                    break
        
        if not id_col:
            raise ValueError("Could not infer id_col. Please specify in config.")
    
    # Infer date_col if not specified
    if not date_col:
        # Look for common date column names
        date_candidates = ['date', 'month', 'time', 'period', 'timestamp']
        for candidate in date_candidates:
            if candidate in df.columns:
                date_col = candidate
                break
        
        if not date_col:
            # Fallback: use first column that can be parsed as date
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        pd.to_datetime(df[col].iloc[:5])  # Test first 5 rows
                        date_col = col
                        break
                    except:
                        continue
        
        if not date_col:
            raise ValueError("Could not infer date_col. Please specify in config.")
    
    print(f"Inferred columns - ID: {id_col}, Date: {date_col}")
    return id_col, date_col


def validate_data_structure(df: pd.DataFrame, id_col: str, date_col: str) -> None:
    """
    Perform structural validation checks on the dataset.
    
    Args:
        df: DataFrame to validate
        id_col: Name of ID column
        date_col: Name of date column
        
    Raises:
        ValueError: If validation checks fail
    """
    print("\n=== Data Structure Validation ===")
    
    # Check required columns exist
    if id_col not in df.columns:
        raise ValueError(f"ID column '{id_col}' not found in data")
    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in data")
    
    # Check for duplicates
    duplicates = df.duplicated(subset=[id_col, date_col]).sum()
    if duplicates > 0:
        raise ValueError(f"Found {duplicates} duplicate (region, date) combinations")
    print(f"[OK] No duplicate (region, date) combinations")
    
    # Check date monotonicity per region
    df_sorted = df.sort_values([id_col, date_col])
    monotonic_issues = 0
    for region in df[id_col].unique():
        region_data = df_sorted[df_sorted[id_col] == region]
        if len(region_data) > 1:
            # Check if dates are monotonically increasing
            dates = pd.to_datetime(region_data[date_col])
            if not dates.is_monotonic_increasing:
                monotonic_issues += 1
    
    if monotonic_issues > 0:
        warnings.warn(f"Found {monotonic_issues} regions with non-monotonic dates")
    else:
        print(f"[OK] Dates are monotonic within each region")
    
    # Check missing rates
    print("\nMissing data rates:")
    missing_rates = df.isnull().mean().sort_values(ascending=False)
    high_missing = missing_rates[missing_rates > 0.2]
    
    for col, rate in missing_rates.items():
        status = "[WARN]" if rate > 0.2 else "[OK]"
        print(f"  {status} {col}: {rate:.1%}")
    
    if len(high_missing) > 0:
        warnings.warn(f"Columns with >20% missing: {list(high_missing.index)}")


def check_target_availability(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[int, str]:
    """
    Check which target columns are available for each horizon.
    
    Args:
        df: DataFrame to check
        config: Configuration dictionary
        
    Returns:
        Dictionary mapping horizon to available target column name
    """
    print("\n=== Target Availability Check ===")
    
    horizons = config.get('targets', {}).get('horizons', [1, 2, 3])
    explicit_cols = config.get('targets', {}).get('explicit_label_cols', {})
    base_target = config.get('targets', {}).get('base_target_col', 'risk_label')
    
    available_targets = {}
    
    for h in horizons:
        # Check for explicit target column
        explicit_col = explicit_cols.get(h)
        if explicit_col and explicit_col in df.columns:
            available_targets[h] = explicit_col
            print(f"[OK] Horizon {h}: Using explicit column '{explicit_col}'")
        elif base_target in df.columns:
            available_targets[h] = base_target
            print(f"[OK] Horizon {h}: Will derive from base target '{base_target}' (shift by +{h})")
        else:
            raise ValueError(f"No target available for horizon {h}. "
                           f"Need either '{explicit_col}' or '{base_target}'")
    
    return available_targets


def summarize_dataset(df: pd.DataFrame, id_col: str, date_col: str) -> None:
    """
    Print a comprehensive summary of the dataset.
    
    Args:
        df: DataFrame to summarize
        id_col: Name of ID column
        date_col: Name of date column
    """
    print("\n=== Dataset Summary ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Data types:\n{df.dtypes}")
    
    print(f"\nRegions ({id_col}):")
    region_counts = df[id_col].value_counts()
    print(f"  Total regions: {len(region_counts)}")
    print(f"  Observations per region: {region_counts.min()}-{region_counts.max()}")
    
    print(f"\nDate range ({date_col}):")
    try:
        dates = pd.to_datetime(df[date_col])
        print(f"  From: {dates.min()}")
        print(f"  To: {dates.max()}")
        print(f"  Unique months: {dates.nunique()}")
    except Exception as e:
        print(f"  Could not parse dates: {e}")
    
    print(f"\nNumeric columns summary:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print(df[numeric_cols].describe())


def validate_dataset(data_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, str, str, Dict[int, str]]:
    """
    Complete dataset validation pipeline.
    
    Args:
        data_path: Path to CSV file
        config: Configuration dictionary
        
    Returns:
        Tuple of (validated_df, id_col, date_col, available_targets)
    """
    if config is None:
        config = {}
    
    # Load data
    df = load_and_validate_data(data_path)
    
    # Infer columns
    id_col, date_col = infer_columns(df, config)
    
    # Validate structure
    validate_data_structure(df, id_col, date_col)
    
    # Check target availability
    available_targets = check_target_availability(df, config)
    
    # Summarize dataset
    summarize_dataset(df, id_col, date_col)
    
    return df, id_col, date_col, available_targets


if __name__ == "__main__":
    # Test the validation pipeline
    import yaml
    
    # Load config
    with open('model/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Run validation
    df, id_col, date_col, targets = validate_dataset(config=config)
    print(f"\nValidation complete!")
    print(f"ID column: {id_col}")
    print(f"Date column: {date_col}")
    print(f"Available targets: {targets}")
