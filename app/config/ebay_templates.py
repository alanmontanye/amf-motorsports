"""
Simplified template formatting functions that provide compatibility
after removing eBay-specific features.
"""

def format_ai_description(part, description_text):
    """
    Simple pass-through function that returns the description text without formatting.
    Kept for API compatibility after removing eBay features.
    
    Args:
        part: The Part object
        description_text: The raw description text
        
    Returns:
        The formatted description (now just returns the raw text)
    """
    # Simply return the description text without eBay-specific formatting
    return description_text
