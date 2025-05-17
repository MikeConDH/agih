"""
Shared utilities for the agents package
"""

def log_emoji(emoji: str, message: str):
    """
    Log a message with an emoji prefix
    
    Args:
        emoji (str): The emoji to use as prefix
        message (str): The message to log
    """
    print(f"{emoji} {message}")

def validate_event(event: dict) -> bool:
    """
    Validate an event dictionary has all required fields
    
    Args:
        event (dict): The event to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["Title", "Date", "URL", "Location", "Type"]
    return all(field in event and event[field] for field in required_fields)

def parse_date(date_str: str) -> bool:
    """
    Validate a date string is in the correct format
    
    Args:
        date_str (str): The date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    try:
        # Expected format: "Monday, May 19, 2025"
        date_pattern = r"^[A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}$"
        return bool(re.match(date_pattern, date_str))
    except:
        return False 