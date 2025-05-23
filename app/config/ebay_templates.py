"""
eBay template configurations for AMF Motorsports
"""

# Default policies to include in all listings
DEFAULT_POLICIES = {
    "shipping": {
        "domestic": "We ship to the continental United States via USPS or UPS, typically within 1-3 business days of payment.",
        "international": "International buyers please contact us for shipping rates before purchasing.",
        "handling_time": "Items typically ship within 1-3 business days after payment is received."
    },
    "returns": {
        "policy": "30-day returns accepted",
        "details": "We accept returns within 30 days. Buyer pays return shipping. Item must be returned in original condition."
    },
    "payment": {
        "methods": "PayPal, Credit Cards",
        "details": "Payment is expected within 3 days of purchase."
    }
}

# Description templates for different part conditions
DESCRIPTION_TEMPLATES = {
    "new": """
{description}

This is a BRAND NEW {part_name} for {atv_year} {atv_make} {atv_model}.
Part Number: {part_number}

ITEM SPECIFICS:
• Condition: New
• Brand: {atv_make} OEM or Aftermarket
• Fitment: {atv_year} {atv_make} {atv_model}
• Part Number: {part_number}

PLEASE NOTE:
• Please verify fitment before purchasing
• Pictures are of the actual item you will receive
    """,
    
    "used_good": """
{description}

This is a USED {part_name} in GOOD CONDITION from a {atv_year} {atv_make} {atv_model}.
Part Number: {part_number}

ITEM SPECIFICS:
• Condition: Used - Good condition
• Shows normal signs of wear but functions perfectly
• Brand: {atv_make} OEM
• Fitment: {atv_year} {atv_make} {atv_model}
• Part Number: {part_number}

PLEASE NOTE:
• Please verify fitment before purchasing
• Pictures are of the actual item you will receive
• May have minor cosmetic imperfections as shown in photos
    """,
    
    "used_fair": """
{description}

This is a USED {part_name} in FAIR CONDITION from a {atv_year} {atv_make} {atv_model}.
Part Number: {part_number}

ITEM SPECIFICS:
• Condition: Used - Fair condition
• Shows visible signs of wear but remains functional
• Brand: {atv_make} OEM
• Fitment: {atv_year} {atv_make} {atv_model}
• Part Number: {part_number}

PLEASE NOTE:
• Please verify fitment before purchasing
• Pictures are of the actual item you will receive
• Has cosmetic wear and imperfections as shown in photos
    """,
    
    "used_poor": """
{description}

This is a USED {part_name} in AS-IS CONDITION from a {atv_year} {atv_make} {atv_model}.
Part Number: {part_number}

ITEM SPECIFICS:
• Condition: Used - Poor/As-Is condition
• Shows significant wear or damage
• Sold for parts or repair purposes
• Brand: {atv_make} OEM
• Fitment: {atv_year} {atv_make} {atv_model}
• Part Number: {part_number}

PLEASE NOTE:
• Sold as-is with no returns
• Please verify fitment before purchasing
• Pictures are of the actual item you will receive
• Has significant wear or damage as shown in photos
    """
}

# HTML wrapper for eBay descriptions including logo and branding
HTML_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
    <!-- Header with Logo -->
    <div style="text-align: center; margin-bottom: 20px; padding: 10px; background-color: #f8f9fa; border-bottom: 3px solid #dc3545;">
        <h1 style="color: #343a40; margin: 0;">AMF Motorsports</h1>
        <p style="color: #6c757d; margin: 5px 0 0 0;">Quality ATV Parts & Accessories</p>
    </div>
    
    <!-- Main Content -->
    <div style="padding: 0 15px;">
        <!-- Description -->
        <div style="margin-bottom: 20px; line-height: 1.6; white-space: pre-line;">
            {main_description}
        </div>
        
        <!-- Policies Section -->
        <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
            <h3 style="color: #343a40; border-bottom: 1px solid #dee2e6; padding-bottom: 10px;">Shipping Information</h3>
            <p>{shipping_domestic}</p>
            <p>{shipping_international}</p>
            <p>{handling_time}</p>
            
            <h3 style="color: #343a40; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; margin-top: 20px;">Return Policy</h3>
            <p><strong>{return_policy}</strong></p>
            <p>{return_details}</p>
            
            <h3 style="color: #343a40; border-bottom: 1px solid #dee2e6; padding-bottom: 10px; margin-top: 20px;">Payment Information</h3>
            <p>We accept: <strong>{payment_methods}</strong></p>
            <p>{payment_details}</p>
        </div>
        
        <!-- Footer -->
        <div style="margin-top: 30px; text-align: center; padding: 15px; border-top: 1px solid #dee2e6;">
            <p style="color: #6c757d;">Thank you for shopping with AMF Motorsports!</p>
            <p style="color: #6c757d;">If you have any questions, please contact us through eBay messaging.</p>
        </div>
    </div>
</div>
"""

def format_ai_description(part, ai_generated_text):
    """
    Format the AI-generated description with the template for the part's condition
    
    Args:
        part: The Part object
        ai_generated_text: The raw text generated by the AI
        
    Returns:
        Formatted HTML description
    """
    # Get the appropriate template based on condition
    condition = part.condition if part.condition in DESCRIPTION_TEMPLATES else "used_fair"
    template = DESCRIPTION_TEMPLATES[condition]
    
    # Format the description template
    main_description = template.format(
        description=ai_generated_text,
        part_name=part.name,
        part_number=part.part_number or "N/A",
        atv_year=part.atv.year if part.atv else "Unknown",
        atv_make=part.atv.make if part.atv else "Unknown",
        atv_model=part.atv.model if part.atv else "Unknown"
    )
    
    # Format the HTML with the description and policies
    html_description = HTML_TEMPLATE.format(
        main_description=main_description,
        shipping_domestic=DEFAULT_POLICIES["shipping"]["domestic"],
        shipping_international=DEFAULT_POLICIES["shipping"]["international"],
        handling_time=DEFAULT_POLICIES["shipping"]["handling_time"],
        return_policy=DEFAULT_POLICIES["returns"]["policy"],
        return_details=DEFAULT_POLICIES["returns"]["details"],
        payment_methods=DEFAULT_POLICIES["payment"]["methods"],
        payment_details=DEFAULT_POLICIES["payment"]["details"]
    )
    
    return html_description
