from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from app import db
from app.models import ATV, Part, Storage
from app.atv.forms import BulkPartForm
import uuid

parts_bulk_bp = Blueprint('parts_bulk', __name__)

@parts_bulk_bp.route('/bulk_add_parts/<int:atv_id>', methods=['GET', 'POST'])
def bulk_add_parts(atv_id):
    """Add multiple parts to an ATV at once"""
    atv = ATV.query.get_or_404(atv_id)
    
    # Get all storage locations for the form
    storage_locations = Storage.query.order_by(Storage.name).all()
    
    # Get unique totes from existing parts for the form
    totes_query = db.session.query(Part.tote).filter(Part.tote.isnot(None)).distinct().order_by(Part.tote)
    existing_totes = [t[0] for t in totes_query.all() if t[0]]
    
    if request.method == 'POST':
        # Get shared data that applies to all parts
        shared_tote = request.form.get('shared_tote')
        shared_storage_id = request.form.get('shared_storage_id')
        
        if shared_storage_id and shared_storage_id.isdigit():
            shared_storage_id = int(shared_storage_id)
        else:
            shared_storage_id = None
            
        # Count how many parts we're adding (look for part_name_X fields)
        parts_count = 0
        parts_added = 0
        
        # Process each part
        for key in request.form:
            if key.startswith('part_name_') and request.form.get(key):
                parts_count += 1
                index = key.split('_')[-1]
                
                try:
                    # Extract part data
                    name = request.form.get(f'part_name_{index}')
                    part_number = request.form.get(f'part_number_{index}')
                    condition = request.form.get(f'condition_{index}')
                    source_price = request.form.get(f'source_price_{index}')
                    list_price = request.form.get(f'list_price_{index}')
                    
                    # Create new part
                    new_part = Part(
                        name=name,
                        part_number=part_number,
                        condition=condition,
                        atv_id=atv_id,
                        tote=shared_tote,
                        storage_id=shared_storage_id,
                    )
                    
                    # Process numeric fields
                    if source_price:
                        try:
                            new_part.source_price = float(source_price)
                        except ValueError:
                            pass
                            
                    if list_price:
                        try:
                            new_part.list_price = float(list_price)
                        except ValueError:
                            pass
                    
                    db.session.add(new_part)
                    parts_added += 1
                    
                except Exception as e:
                    flash(f'Error adding part {name}: {str(e)}', 'danger')
        
        if parts_added > 0:
            # If this is the first part added, change ATV status to parting_out if it's still whole
            if atv.parting_status == 'whole':
                atv.parting_status = 'parting_out'
                
            db.session.commit()
            flash(f'Successfully added {parts_added} parts to {atv.year} {atv.make} {atv.model}', 'success')
            
            # Redirect to the parts list for this ATV
            return redirect(url_for('atv.atv_parts', atv_id=atv_id))
        else:
            flash('No valid parts were added. Please check your input.', 'warning')
    
    return render_template(
        'atv/parts/bulk_add.html',
        title=f'Bulk Add Parts - {atv.year} {atv.make} {atv.model}',
        atv=atv,
        storage_locations=storage_locations,
        existing_totes=existing_totes
    )
