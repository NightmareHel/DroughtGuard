"""
Risk categorization utilities for DroughtGuard.
"""

from typing import Dict, Any, Optional


def get_default_thresholds() -> Dict[str, Dict[str, float]]:
    """Get default risk thresholds for each horizon."""
    return {
        'h1': {'red': 0.60, 'yellow': 0.35},
        'h2': {'red': 0.57, 'yellow': 0.33},
        'h3': {'red': 0.55, 'yellow': 0.30}
    }


def categorize_risk(probability: float, horizon: int = 1, 
                   thresholds: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
    """
    Categorize risk probability into levels using horizon-specific thresholds.
    
    Args:
        probability (float): Risk probability between 0 and 1
        horizon (int): Prediction horizon (1, 2, or 3 months)
        thresholds (dict, optional): Threshold configuration. If None, loads from config.
    
    Returns:
        dict: Risk category with label, color, and metadata
    """
    if thresholds is None:
        thresholds = get_default_thresholds()
    
    # Get thresholds for this horizon
    horizon_key = f'h{horizon}'
    if horizon_key not in thresholds:
        # Fallback to h1 thresholds
        horizon_key = 'h1'
    
    horizon_thresholds = thresholds.get(horizon_key, {'red': 0.6, 'yellow': 0.35})
    red_thresh = horizon_thresholds.get('red', 0.6)
    yellow_thresh = horizon_thresholds.get('yellow', 0.35)
    
    # Categorize based on thresholds
    if probability >= red_thresh:
        return {
            'label': 'High',
            'color': '#dc3545',  # Red
            'level': 3,
            'threshold_used': red_thresh,
            'horizon': horizon
        }
    elif probability >= yellow_thresh:
        return {
            'label': 'Moderate', 
            'color': '#ffc107',  # Yellow
            'level': 2,
            'threshold_used': yellow_thresh,
            'horizon': horizon
        }
    else:
        return {
            'label': 'Low',
            'color': '#28a745',  # Green
            'level': 1,
            'threshold_used': yellow_thresh,
            'horizon': horizon
        }


def categorize_forecasts(forecasts_df, thresholds: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
    """
    Categorize a DataFrame of forecasts with probabilities and horizons.
    
    Args:
        forecasts_df: DataFrame with columns 'prob', 'horizon', and optionally 'region'
        thresholds (dict, optional): Threshold configuration
    
    Returns:
        dict: Summary statistics and categorized forecasts
    """
    if thresholds is None:
        thresholds = get_default_thresholds()
    
    results = {
        'summary': {},
        'by_horizon': {},
        'by_region': {}
    }
    
    # Overall summary
    total_forecasts = len(forecasts_df)
    results['summary']['total_forecasts'] = total_forecasts
    
    # Summary by horizon
    for horizon in forecasts_df['horizon'].unique():
        h_forecasts = forecasts_df[forecasts_df['horizon'] == horizon]
        h_categories = [categorize_risk(prob, horizon, thresholds) for prob in h_forecasts['prob']]
        
        h_summary = {
            'count': len(h_forecasts),
            'avg_probability': h_forecasts['prob'].mean(),
            'risk_distribution': {}
        }
        
        # Count risk levels
        for cat in h_categories:
            level = cat['label']
            h_summary['risk_distribution'][level] = h_summary['risk_distribution'].get(level, 0) + 1
        
        results['by_horizon'][f'h{horizon}'] = h_summary
    
    # Summary by region (if region column exists)
    if 'region' in forecasts_df.columns:
        for region in forecasts_df['region'].unique():
            r_forecasts = forecasts_df[forecasts_df['region'] == region]
            r_categories = [categorize_risk(prob, h, thresholds) for prob, h in zip(r_forecasts['prob'], r_forecasts['horizon'])]
            
            r_summary = {
                'count': len(r_forecasts),
                'avg_probability': r_forecasts['prob'].mean(),
                'max_risk_level': max([cat['level'] for cat in r_categories]) if r_categories else 0,
                'risk_distribution': {}
            }
            
            # Count risk levels
            for cat in r_categories:
                level = cat['label']
                r_summary['risk_distribution'][level] = r_summary['risk_distribution'].get(level, 0) + 1
            
            results['by_region'][region] = r_summary
    
    return results


def get_risk_color(risk_level: str) -> str:
    """Get color code for a risk level."""
    color_map = {
        'Low': '#28a745',
        'Moderate': '#ffc107', 
        'High': '#dc3545'
    }
    return color_map.get(risk_level, '#6c757d')  # Default gray


def get_risk_icon(risk_level: str) -> str:
    """Get icon/emoji for a risk level."""
    icon_map = {
        'Low': '🟢',
        'Moderate': '🟡',
        'High': '🔴'
    }
    return icon_map.get(risk_level, '⚪')  # Default white circle
