"""
Risk categorization utilities.
"""
def categorize_risk(probability):
    """
    Categorize risk probability into levels.
    
    Args:
        probability (float): Risk probability between 0 and 1
    
    Returns:
        dict: Risk category with color and label
    """
    if probability < 0.33:
        return {
            'label': 'Low',
            'color': '#28a745'  # Green
        }
    elif probability < 0.67:
        return {
            'label': 'Moderate',
            'color': '#ffc107'  # Yellow
        }
    else:
        return {
            'label': 'High',
            'color': '#dc3545'  # Red
        }
