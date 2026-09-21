import re

def analyze_priority(title: str, description: str, category: str):
    """
    Analyzes the complaint details and returns (Priority, Reason).
    Priority can be Critical, High, Medium, Low.
    """
    text = (title + " " + description + " " + category).lower()
    
    # Priority mapping according to the specified examples
    critical_keywords = ['fire', 'accident', 'gas leak', 'building collapse', 'collapse', 'electrocution', 'flood', 'medical emergency', 'emergency', 'life threatening']
    high_keywords = ['water leakage', 'water leak', 'power failure', 'road damage', 'sewage overflow', 'sewage', 'outage', 'blockage']
    medium_keywords = ['garbage', 'street light', 'public cleanliness', 'cleanliness', 'pothole', 'noise']
    low_keywords = ['suggestion', 'query', 'general', 'cosmetic', 'inquiry', 'feedback']
    
    # Check Critical
    for kw in critical_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return 'Critical', f'AI detected critical keyword: "{kw}". Immediate attention required.'
            
    # Check High
    for kw in high_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return 'High', f'AI detected high priority keyword: "{kw}". Quick resolution needed.'
            
    # Check Medium
    for kw in medium_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return 'Medium', f'AI detected medium priority keyword: "{kw}". Standard SLA applies.'
            
    # Check Low
    for kw in low_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return 'Low', f'AI detected low priority keyword: "{kw}". Routine processing.'
            
    # Default fallback
    if category == 'Emergency/Safety':
        return 'Critical', 'Assigned Critical based on Emergency category.'
    elif category == 'Utilities (Water/Electricity)':
        return 'High', 'Assigned High based on Utility category.'
    elif category == 'Sanitation & Waste':
        return 'Medium', 'Assigned Medium based on Sanitation category.'
    else:
        return 'Low', 'No specific urgent keywords detected. Defaulting to Low priority.'
