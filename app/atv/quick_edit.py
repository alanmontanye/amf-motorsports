from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Part, Storage
from app.utils import admin_required
from app.atv.forms import QuickEditPartForm

quick_edit_bp = Blueprint('quick_edit', __name__)

@quick_edit_bp.route('/part/quick_edit/<int:part_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def quick_edit_part(part_id):
    """Quick edit a part with minimal fields for fast updates"""
    part = Part.query.get_or_404(part_id)
    form = QuickEditPartForm(obj=part)
    
    # Handle form submission
    if request.method == 'POST':
        if form.validate_on_submit():
            form.populate_obj(part)
            db.session.commit()
            
            # If this is an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'Part "{part.name}" updated successfully',
                    'part': {
                        'id': part.id,
                        'name': part.name,
                        'condition': part.condition,
                        'status': part.status,
                        'tote': part.tote,
                        'list_price': part.list_price
                    }
                })
            
            # For regular form submissions, redirect back to the part list
            flash(f'Part "{part.name}" updated successfully', 'success')
            if part.atv_id:
                return redirect(url_for('atv.atv_parts', atv_id=part.atv_id))
            else:
                return redirect(url_for('atv.parts_list'))
        
        # Handle validation errors
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'errors': form.errors
            }), 400
    
    # If this is an AJAX request, return just the form HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('atv/parts/quick_edit_form.html', form=form, part=part)
    
    # For regular GET requests, render the full page
    return render_template('atv/parts/quick_edit.html', form=form, part=part)


@quick_edit_bp.route('/part/inline_edit/<int:part_id>', methods=['GET'])
@login_required
@admin_required
def get_inline_edit_form(part_id):
    """Get the inline edit form for a part via AJAX"""
    part = Part.query.get_or_404(part_id)
    form = QuickEditPartForm(obj=part)
    return render_template('atv/parts/quick_edit_form.html', form=form, part=part)
