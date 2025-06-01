from flask import render_template, redirect, url_for, request, current_app, flash, jsonify
from werkzeug.utils import secure_filename
import os
from app.atv import bp
from app.models import ATV, Part, Image, Storage
from app import db
from app.atv.forms import PartForm
from datetime import datetime
from app.atv.ebay import bp as ebay_bp

@bp.route('/parts')
def parts_list():
    """Show all parts with advanced filtering and sorting options"""
    # Get filter parameters
    atv_id = request.args.get('atv_id', type=int)
    storage_id = request.args.get('storage_id', type=int)
    status = request.args.get('status')
    condition = request.args.get('condition')
    platform = request.args.get('platform')
    tote = request.args.get('tote')
    sort_by = request.args.get('sort_by', 'newest')
    view_mode = request.args.get('view_mode', 'grid')

    # Start with base query
    query = Part.query.join(ATV)

    # Apply filters
    if atv_id:
        query = query.filter(Part.atv_id == atv_id)
    else:
        # Only show parts from ATVs that are being parted out or have been parted out
        query = query.filter(ATV.parting_status.in_(['parting_out', 'parted_out']))

    if storage_id:
        query = query.filter(Part.storage_id == storage_id)
    if status:
        query = query.filter(Part.status == status)
    if condition:
        query = query.filter(Part.condition == condition)
    if platform:
        query = query.filter(Part.platform == platform)
    if tote:
        query = query.filter(Part.tote == tote)

    # Apply sorting
    if sort_by == 'newest':
        query = query.order_by(Part.created_at.desc())
    elif sort_by == 'price_asc':
        query = query.order_by(Part.list_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Part.list_price.desc())
    elif sort_by == 'name':
        query = query.order_by(Part.name.asc())
    elif sort_by == 'tote':
        query = query.order_by(Part.tote.asc(), Part.name.asc())
    elif sort_by == 'atv':
        query = query.order_by(ATV.year.desc(), ATV.make.asc(), ATV.model.asc(), Part.name.asc())

    # Execute query
    parts = query.all()

    # Get list of ATVs being parted out
    parting_atvs = ATV.query.filter(ATV.parting_status.in_(['parting_out', 'parted_out'])).order_by(
        ATV.year.desc(), ATV.make.asc(), ATV.model.asc()
    ).all()

    # Get all storage locations
    storages = Storage.query.order_by(Storage.name.asc()).all()
    
    # Get distinct totes for filtering
    distinct_totes = db.session.query(Part.tote).distinct().filter(Part.tote.isnot(None))
    totes = [t[0] for t in distinct_totes if t[0]] # Filter out None/empty values
    totes.sort()

    # Calculate total value
    total_value = sum(
        part.list_price if part.status != 'sold' else part.sold_price
        for part in parts
        if (part.status != 'sold' and part.list_price) or (part.status == 'sold' and part.sold_price)
    )
    
    # Get status counts for summary
    status_counts = {
        'all': len(parts),
        'in_stock': sum(1 for part in parts if part.status == 'in_stock'),
        'listed': sum(1 for part in parts if part.status == 'listed'),
        'reserved': sum(1 for part in parts if part.status == 'reserved'),
        'sold': sum(1 for part in parts if part.status == 'sold')
    }

    template_vars = {
        'title': 'Parts List',
        'parts': parts,
        'parting_atvs': parting_atvs,
        'storages': storages,
        'totes': totes,
        'total_value': total_value,
        'status_counts': status_counts,
        'selected_atv_id': atv_id,
        'selected_storage_id': storage_id,
        'selected_status': status,
        'selected_condition': condition,
        'selected_platform': platform,
        'selected_tote': tote,
        'sort_by': sort_by,
        'view_mode': view_mode
    }
    
    # Try the template with view_mode first, then fall back to regular template
    templates_to_try = [
        f'atv/parts/index_{view_mode}.html',  # View-mode specific (grid/list/table)
        'atv/parts/index.html',               # Original path
        'atv/parts_list.html',                # Alternative name
    ]
    
    # Try each template in order
    last_error = None
    for template in templates_to_try:
        try:
            return render_template(template, **template_vars)
        except Exception as e:
            current_app.logger.error(f"Failed to render template {template}: {str(e)}")
            last_error = e
    
    # If we get here, none of the templates worked, use a simplified fallback
    return render_template('atv/parts_error.html', error=str(last_error), **template_vars)

@bp.route('/<int:atv_id>/parts')
def atv_parts(atv_id):
    """Show parts for a specific ATV"""
    atv = ATV.query.get_or_404(atv_id)
    
    template_vars = {
        'title': f'Parts - {atv.year} {atv.make} {atv.model}',
        'atv': atv
    }
    
    # Try several template paths in order
    templates_to_try = [
        'atv/parts/atv_parts.html',   # Original path
        'atv/part/atv_parts.html',    # Alternative path (no 's')
        'atv/atv_parts.html',         # Flattened path
        'atv/parts.html',             # Simplified path
        'atv/parts_error.html'        # Error fallback
    ]
    
    # Try each template in order
    last_error = None
    for template in templates_to_try:
        try:
            return render_template(template, **template_vars)
        except Exception as e:
            current_app.logger.error(f"Failed to render template {template}: {str(e)}")
            last_error = e
    
    # If we get here, none of the templates worked, so show a basic parts list
    return f"<h1>Parts for {atv.year} {atv.make} {atv.model}</h1><p>Error loading parts template: {str(last_error)}</p>"

def handle_image_upload(files, part):
    """Helper function to handle image uploads"""
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
            image = Image(
                filename=filename,
                part=part
            )
            db.session.add(image)

@bp.route('/<int:atv_id>/parts/add', methods=['GET', 'POST'])
def add_part(atv_id):
    """Add a new part to an ATV"""
    atv = ATV.query.get_or_404(atv_id)
    form = PartForm()
    
    # Set storage choices
    storages = Storage.query.order_by(Storage.name).all()
    form.storage_id.choices = [(0, 'None')] + [(s.id, s.name) for s in storages]
    
    if form.validate_on_submit():
        storage_id = form.storage_id.data if form.storage_id.data != 0 else None
        
        # Create part with basic info
        part = Part(
            name=form.name.data,
            part_number=form.part_number.data,
            condition=form.condition.data,
            storage_id=storage_id,
            location=form.location.data,
            status=form.status.data,
            source_price=form.source_price.data,
            list_price=form.list_price.data,
            description=form.description.data,
            atv=atv
        )
        
        # If part is being listed
        if form.status.data == 'listed':
            part.platform = form.platform.data
            part.listing_url = form.listing_url.data
        
        # If part is being marked as sold
        if form.status.data == 'sold':
            part.sold_price = form.sold_price.data
            part.sold_date = form.sold_date.data or datetime.now()
            part.shipping_cost = form.shipping_cost.data
            part.platform_fees = form.platform_fees.data
            part.platform = form.platform.data
            
            # Calculate profit
            profit = (part.sold_price or 0) - (part.source_price or 0) - (part.shipping_cost or 0) - (part.platform_fees or 0)
            
            # Update ATV's earnings - handle case where total_earnings doesn't exist yet
            try:
                atv.total_earnings = (atv.total_earnings or 0) + profit
            except:
                # If total_earnings doesn't exist, just continue
                pass
            
        db.session.add(part)
        db.session.commit()

        # Handle image uploads
        if 'images[]' in request.files:
            files = request.files.getlist('images[]')
            handle_image_upload(files, part)
            db.session.commit()

        flash('Part added successfully!', 'success')
        return redirect(url_for('atv.view_part', id=part.id))
    
    template_vars = {
        'title': 'Add Part',
        'form': form,
        'atv': atv
    }
    
    # Try several template paths in order
    templates_to_try = [
        'atv/parts/form.html',     # Original path
        'atv/part/form.html',      # Alternative path (no 's')
        'atv/form_parts.html',     # Flattened path
        'atv/form.html',           # Simplified path
        'atv/parts_error.html'     # Error fallback
    ]
    
    # Try each template in order
    last_error = None
    for template in templates_to_try:
        try:
            return render_template(template, **template_vars)
        except Exception as e:
            current_app.logger.error(f"Failed to render template {template}: {str(e)}")
            last_error = e
    
    # If we get here, none of the templates worked, so show the simplest possible error
    # Create a very basic form to add a part without using templates
    html = f"""
    <h1>Add Part - Simple Form</h1>
    <p><em>Using emergency fallback form - templates could not be loaded: {str(last_error)}</em></p>
    <form method="POST" enctype="multipart/form-data">
        {form.csrf_token}
        <div style="margin-bottom: 15px;">
            <label>Name:</label><br>
            {form.name(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Part Number:</label><br>
            {form.part_number(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Condition:</label><br>
            {form.condition(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Status:</label><br>
            {form.status(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Description:</label><br>
            {form.description(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Source Price:</label><br>
            {form.source_price(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <button type="submit" class="btn btn-primary">Add Part</button>
            <a href="{url_for('atv.view_atv', id=atv.id)}" class="btn btn-secondary">Cancel</a>
    </form>
    """
    return html

@bp.route('/part/<int:part_id>/edit', methods=['GET', 'POST'])
def edit_part(part_id):
    part = Part.query.get_or_404(part_id)
    form = PartForm(obj=part)
    
    # Get available ATVs and storage locations for selection
    form.atv_id.choices = [(a.id, f"{a.year} {a.make} {a.model}") for a in ATV.query.all()]
    form.storage_id.choices = [(0, 'None')] + [(s.id, s.name) for s in Storage.query.all()]
    
    if form.validate_on_submit():
        form.populate_obj(part)
        
        # Calculate/update any derived values
        if part.status == 'sold' and part.sold_price and part.list_price:
            # Calculate profit margin
            part.profit_margin = (part.sold_price - part.list_price) / part.list_price * 100 if part.list_price > 0 else 0
        if form.status.data == 'listed':
            part.platform = form.platform.data
            part.listing_url = form.listing_url.data
            # Clear sold info if part was previously sold
            part.sold_price = None
            part.sold_date = None
            part.shipping_cost = None
            part.platform_fees = None
        
        # Handle sold info
        if form.status.data == 'sold':
            part.sold_price = form.sold_price.data
            part.sold_date = form.sold_date.data or datetime.now()
            part.shipping_cost = form.shipping_cost.data
            part.platform_fees = form.platform_fees.data
            part.platform = form.platform.data
            
            # Calculate new profit
            new_profit = (part.sold_price or 0) - (part.source_price or 0) - (part.shipping_cost or 0) - (part.platform_fees or 0)
            
            # Update ATV's earnings - handle case where total_earnings doesn't exist yet
            try:
                # Subtract old profit, add new profit
                part.atv.total_earnings = (getattr(part.atv, 'total_earnings', 0) or 0) - old_profit + new_profit
            except:
                # If total_earnings doesn't exist, just continue
                pass
            
        else:
            # If part is no longer sold, subtract the old profit from ATV earnings
            if part.status != 'sold' and old_profit != 0:
                try:
                    part.atv.total_earnings = (getattr(part.atv, 'total_earnings', 0) or 0) - old_profit
                except:
                    pass
                # Clear sold info
                part.sold_price = None
                part.sold_date = None
                part.shipping_cost = None
                part.platform_fees = None

        # Handle image uploads
        if 'images[]' in request.files:
            files = request.files.getlist('images[]')
            handle_image_upload(files, part)

        # Handle image deletions
        if 'delete_images[]' in request.form:
            image_ids = request.form.getlist('delete_images[]')
            for image_id in image_ids:
                image = Image.query.get(image_id)
                if image and image.part_id == part.id:
                    # Delete the file
                    try:
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
                    except:
                        pass  # File might not exist
                    db.session.delete(image)

        db.session.commit()
        flash('Part updated successfully!', 'success')
        return redirect(url_for('atv.view_part', id=part.id))
    
    # Set initial storage value
    if part.storage_id:
        form.storage_id.data = part.storage_id
    else:
        form.storage_id.data = 0
    
    # Add the images to the form in case of validation errors
    template_vars = {
        'title': 'Edit Part',
        'form': form,
        'part': part,
        'id': id
    }
    
    # Try several template paths in order
    templates_to_try = [
        'atv/parts/form.html',     # Original path
        'atv/part/form.html',      # Alternative path (no 's')
        'atv/form_parts.html',     # Flattened path
        'atv/form.html',           # Simplified path
        'atv/parts_error.html'     # Error fallback
    ]
    
    # Try each template in order
    last_error = None
    for template in templates_to_try:
        try:
            return render_template(template, **template_vars)
        except Exception as e:
            current_app.logger.error(f"Failed to render template {template}: {str(e)}")
            last_error = e
    
    # If we get here, none of the templates worked, so show a basic fallback form
    html = f"""
    <h1>Edit Part - Simple Form</h1>
    <p><em>Using emergency fallback form - templates could not be loaded: {str(last_error)}</em></p>
    <form method="POST" enctype="multipart/form-data">
        {form.csrf_token}
        <div style="margin-bottom: 15px;">
            <label>Name:</label><br>
            {form.name(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Part Number:</label><br>
            {form.part_number(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Condition:</label><br>
            {form.condition(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Status:</label><br>
            {form.status(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Description:</label><br>
            {form.description(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <label>Source Price:</label><br>
            {form.source_price(class_="form-control")}
        </div>
        <div style="margin-bottom: 15px;">
            <button type="submit" class="btn btn-primary">Save Changes</button>
            <a href="{url_for('atv.view_part', id=part.id)}" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
    """
    return html

@bp.route('/part/<int:id>/unsell', methods=['POST'])
def unsell_part(id):
    """Mark a part as unsold (back to in stock)"""
    part = Part.query.get_or_404(id)
    
    # Find and update any associated listings
    if part.platform == 'ebay':
        for listing in part.ebay_listings:
            if listing.status == 'sold':
                listing.status = 'ended'
                
    # Reset part sale data
    part.status = 'in_stock'
    part.platform = None
    part.sold_price = None
    part.sold_date = None
    part.shipping_cost = None
    part.platform_fees = None
    
    # Update ATV earnings if applicable
    if part.atv and hasattr(part.atv, 'total_earnings') and part.atv.total_earnings is not None:
        # Calculate what this part contributed to earnings and subtract it
        original_profit = part.net_profit()
        part.atv.total_earnings -= original_profit
    
    db.session.commit()
    
    flash('Part has been marked as unsold and returned to inventory.', 'success')
    return redirect(url_for('atv.view_part', id=part.id))

@bp.route('/part/<int:id>/delete', methods=['POST'])
def delete_part(id):
    """Delete a part and its associated images"""
    part = Part.query.get_or_404(id)
    atv_id = part.atv_id
    
    # Delete associated images first
    for image in part.images:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
        except:
            pass  # File might not exist
        db.session.delete(image)
    
    # Delete the part
    db.session.delete(part)
    db.session.commit()
    
    flash('Part deleted successfully!', 'success')
    return redirect(url_for('atv.atv_parts', atv_id=atv_id))

@bp.route('/part/<int:id>/image/delete/<int:image_id>', methods=['POST'])
def delete_part_image(id, image_id):
    """Delete a specific image from a part"""
    part = Part.query.get_or_404(id)
    image = Image.query.get_or_404(image_id)
    
    # Verify the image belongs to the part
    if image.part_id != part.id:
        flash('Invalid image!', 'error')
        return redirect(url_for('atv.view_part', id=id))
    
    # Delete the file
    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
    except:
        pass  # File might not exist
    
    # Delete the database record
    db.session.delete(image)
    db.session.commit()
    
    flash('Image deleted successfully!', 'success')
    return redirect(url_for('atv.view_part', id=id))

@bp.route('/part/<int:id>')
def view_part(id):
    """View part details"""
    part = Part.query.get_or_404(id)
    return render_template('atv/parts/view.html', title=f'View Part - {part.name}', part=part)

@bp.route('/part/<int:id>/image/upload', methods=['POST'])
def upload_part_image(id):
    """Upload additional images for a part"""
    part = Part.query.get_or_404(id)
    
    if 'images[]' in request.files:
        files = request.files.getlist('images[]')
        handle_image_upload(files, part)
        db.session.commit()
        flash('Images uploaded successfully!', 'success')
    else:
        flash('No images selected!', 'error')
    
    return redirect(url_for('atv.view_part', id=id))


@bp.route('/part/<int:id>/quick-edit', methods=['GET', 'POST'])
def quick_edit_part(id):
    """Quick inline editing of a part with minimal fields"""
    from app.atv.forms import QuickEditPartForm
    
    part = Part.query.get_or_404(id)
    form = QuickEditPartForm(obj=part)
    
    # Handle AJAX requests differently
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Update only the fields in the quick edit form
            part.name = form.name.data
            part.condition = form.condition.data
            part.status = form.status.data
            part.tote = form.tote.data
            part.list_price = form.list_price.data
            
            # Only set listing_date if we're changing to 'listed' status
            if part.status == 'listed' and not part.listing_date:
                part.listing_date = datetime.utcnow()
            
            db.session.commit()
            
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'Part updated successfully',
                    'part': {
                        'id': part.id,
                        'name': part.name,
                        'condition': part.condition,
                        'status': part.status,
                        'tote': part.tote,
                        'list_price': part.list_price
                    }
                })
            
            flash('Part updated successfully!', 'success')
            # Determine where to redirect based on where the request came from
            next_page = request.args.get('next') or url_for('atv.view_part', id=id)
            return redirect(next_page)
        elif is_ajax:
            return jsonify({'success': False, 'errors': form.errors}), 400
    
    if is_ajax:
        return render_template('atv/parts/quick_edit_form.html', form=form, part=part)
    
    return render_template('atv/parts/quick_edit.html', form=form, part=part)


@bp.route('/bulk-add-parts', methods=['GET', 'POST'])
def bulk_add_parts():
    """Add multiple parts at once with shared properties like tote/ATV"""
    from app.atv.forms import BulkPartForm
    
    form = BulkPartForm()
    
    # Set ATV and storage location choices
    form.atv_id.choices = [(a.id, f"{a.year} {a.make} {a.model}") 
                         for a in ATV.query.filter(ATV.parting_status.in_(['whole', 'parting_out'])).all()]
    form.storage_id.choices = [(0, 'None')] + [(s.id, s.name) for s in Storage.query.all()]
    
    if request.method == 'POST':
        # Process the bulk form itself
        if form.validate_on_submit():
            atv_id = form.atv_id.data
            storage_id = form.storage_id.data if form.storage_id.data != 0 else None
            tote = form.tote.data
            
            # Get the names and prices for each part from the form
            part_names = request.form.getlist('part_name[]')
            part_conditions = request.form.getlist('part_condition[]')
            part_prices = request.form.getlist('part_price[]')
            part_descriptions = request.form.getlist('part_description[]')
            
            # Mark the ATV as parting_out if it's currently whole
            atv = ATV.query.get_or_404(atv_id)
            if atv.parting_status == 'whole':
                atv.parting_status = 'parting_out'
            
            # Create each part
            parts_added = 0
            for i in range(len(part_names)):
                if part_names[i].strip():  # Only process non-empty names
                    price = float(part_prices[i]) if part_prices[i] and part_prices[i].strip() else None
                    
                    part = Part(
                        name=part_names[i].strip(),
                        condition=part_conditions[i] if i < len(part_conditions) else 'used_good',
                        tote=tote,
                        list_price=price,
                        description=part_descriptions[i] if i < len(part_descriptions) else '',
                        atv_id=atv_id,
                        storage_id=storage_id,
                        status='in_stock'
                    )
                    db.session.add(part)
                    parts_added += 1
            
            if parts_added > 0:
                db.session.commit()
                flash(f'{parts_added} parts added successfully!', 'success')
                return redirect(url_for('atv.atv_parts', atv_id=atv_id))
            else:
                flash('No valid parts were found to add.', 'warning')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    # Get the pre-selected ATV if specified in query parameters
    selected_atv_id = request.args.get('atv_id', type=int)
    if selected_atv_id:
        form.atv_id.data = selected_atv_id
    
    return render_template('atv/parts/bulk_add.html', form=form, title='Bulk Add Parts')
