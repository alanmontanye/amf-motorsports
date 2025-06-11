"""
AI-powered description generator for parts listings
"""
from flask import request, jsonify, render_template, redirect, url_for, flash, current_app
from app.atv import bp
from app.models import Part, ATV
from app import db
import openai
# Removed eBay-specific imports
import json

def generate_part_description(part):
    """
    Generate an AI-powered description for a part based on its details
    
    Args:
        part: The Part object to generate a description for
        
    Returns:
        AI-generated description text
    """
    try:
        # Get the OpenAI API key from app config
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            return "Error: OpenAI API key not configured. Please set OPENAI_API_KEY in your environment variables."
        
        # Set up the OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Prepare context about the part
        part_context = {
            "name": part.name,
            "part_number": part.part_number or "Unknown",
            "condition": part.condition,
            "atv_year": part.atv.year if part.atv else "",
            "atv_make": part.atv.make if part.atv else "",
            "atv_model": part.atv.model if part.atv else "",
            "description": part.description or ""
        }
        
        # Create prompt for the AI
        prompt = f"""
        Write a detailed, factual, and professional description for the following ATV part that will be listed on eBay:
        
        Part Name: {part_context['name']}
        Part Number: {part_context['part_number']}
        Condition: {part_context['condition']}
        ATV: {part_context['atv_year']} {part_context['atv_make']} {part_context['atv_model']}
        Current Description: {part_context['description']}
        
        Focus on:
        1. The part's function and compatibility
        2. Any notable features
        3. Why someone would need this part
        4. Accurate technical details
        
        Use factual language appropriate for the condition. Keep the description under 150 words.
        DO NOT fabricate details or specifications that aren't provided.
        """
        
        # Make the API request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes professional and accurate eBay listings for ATV parts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        # Extract the generated text
        ai_description = response.choices[0].message.content.strip()
        
        return ai_description
        
    except Exception as e:
        current_app.logger.error(f"Error generating AI description: {str(e)}")
        return f"Error generating description: {str(e)}"


@bp.route('/part/<int:part_id>/generate-description', methods=['POST'])
def generate_description(part_id):
    """
    Generate an AI description for a part and show a preview
    """
    part = Part.query.get_or_404(part_id)
    
    try:
        # Generate the description
        ai_description = generate_part_description(part)
        
        # Store in session for preview
        if isinstance(ai_description, str) and not ai_description.startswith("Error:"):
            # Simplified to use raw description without eBay formatting
            formatted_description = ai_description
            return render_template('atv/parts/description_preview.html', 
                                   part=part, 
                                   raw_description=ai_description,
                                   formatted_description=formatted_description)
        else:
            flash(ai_description, 'error')
            return redirect(url_for('atv.view_part', id=part_id))
            
    except Exception as e:
        flash(f"Error generating description: {str(e)}", 'error')
        return redirect(url_for('atv.view_part', id=part_id))


@bp.route('/part/<int:part_id>/apply-description', methods=['POST'])
def apply_description(part_id):
    """
    Apply the AI-generated description to the part
    """
    part = Part.query.get_or_404(part_id)
    
    # Get the description from the form
    raw_description = request.form.get('raw_description')
    formatted_description = request.form.get('formatted_description')
    
    if not raw_description or not formatted_description:
        flash("Missing description data", 'error')
        return redirect(url_for('atv.view_part', id=part_id))
    
    try:
        # Update the part with the new description (removed eBay-specific field)
        part.description = raw_description
        db.session.commit()
        
        flash("AI description applied successfully!", 'success')
        return redirect(url_for('atv.view_part', id=part_id))
        
    except Exception as e:
        flash(f"Error applying description: {str(e)}", 'error')
        return redirect(url_for('atv.view_part', id=part_id))
