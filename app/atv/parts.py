from flask import render_template, redirect, url_for, request, current_app, flash
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
    sort_by = request.args.get('sort_by', 'newest')

    # Start with base query
    query = Part.query.join(ATV)

    # Apply filters
    if atv_id:
        query = query.filter(Part.atv_id == atv_id)
    else:
        # Only show parts from ATVs that are being parted out or have been parted out
        query = query.filter(ATV.status.in_(['parting_out', 'parted_out']))

    if storage_id:
        query = query.filter(Part.storage_id == storage_id)
    if status:
        query = query.filter(Part.status == status)
    if condition:
        query = query.filter(Part.condition == condition)
    if platform:
        query = query.filter(Part.platform == platform)

    # Apply sorting
    if sort_by == 'newest':
        query = query.order_by(Part.created_at.desc())
    elif sort_by == 'price_asc':
        query = query.order_by(Part.list_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Part.list_price.desc())
    elif sort_by == 'name':
        query = query.order_by(Part.name.asc())

    # Execute query
    parts = query.all()

    # Get list of ATVs being parted out
    parting_atvs = ATV.query.filter(ATV.status.in_(['parting_out', 'parted_out'])).order_by(
        ATV.year.desc(), ATV.make.asc(), ATV.model.asc()
    ).all()

    # Get all storage locations
    storages = Storage.query.order_by(Storage.name.asc()).all()

    # Calculate total value
    total_value = sum(
        part.list_price if part.status != 'sold' else part.sold_price
        for part in parts
        if (part.status != 'sold' and part.list_price) or (part.status == 'sold' and part.sold_price)
    )

    return render_template('atv/parts/index.html',
                         title='Parts List',
                         parts=parts,
                         parting_atvs=parting_atvs,
                         storages=storages,
                         total_value=total_value,
                         selected_atv_id=atv_id,
                         selected_storage_id=storage_id,
                         selected_status=status,
                         selected_condition=condition,
                         selected_platform=platform,
                         sort_by=sort_by)

@bp.route('/<int:atv_id>/parts')
def atv_parts(atv_id):
    """Show parts for a specific ATV"""
    atv = ATV.query.get_or_404(atv_id)
    return render_template('atv/parts/atv_parts.html', title=f'Parts - {atv.year} {atv.make} {atv.model}', atv=atv)

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
    
    return render_template('atv/parts/form.html', title='Add Part', form=form, atv=atv)

@bp.route('/part/<int:id>/edit', methods=['GET', 'POST'])
def edit_part(id):
    """Edit part details"""
    part = Part.query.get_or_404(id)
    form = PartForm(obj=part)
    
    # Set storage choices
    storages = Storage.query.order_by(Storage.name).all()
    form.storage_id.choices = [(0, 'None')] + [(s.id, s.name) for s in storages]
    
    if form.validate_on_submit():
        # Calculate old profit if part was sold
        old_profit = 0
        if part.status == 'sold':
            old_profit = (part.sold_price or 0) - (part.source_price or 0) - (part.shipping_cost or 0) - (part.platform_fees or 0)
        
        # Update basic info
        storage_id = form.storage_id.data if form.storage_id.data != 0 else None
        part.name = form.name.data
        part.part_number = form.part_number.data
        part.condition = form.condition.data
        part.storage_id = storage_id
        part.location = form.location.data
        part.status = form.status.data
        part.source_price = form.source_price.data
        part.list_price = form.list_price.data
        part.description = form.description.data

        # Handle listing info
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
    
    return render_template('atv/parts/form.html', title='Edit Part', form=form, part=part)

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
