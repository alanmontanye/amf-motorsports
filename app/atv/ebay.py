"""eBay integration routes"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from app.atv import bp
from app.models import Part, EbayListing, Image, ATV, EbayCredentials, EbayCategory, EbayTemplate
from app.atv.ebay_forms import EbayListingForm
from app import db
from datetime import datetime
import json
import calendar
import logging
from app.atv.ebay_api import EbayListingManager

@bp.route('/ebay/bulk-list', methods=['POST'])
def bulk_list_on_ebay():
    """Create eBay listings for multiple parts at once"""
    part_ids = request.form.getlist('part_ids')
    
    if not part_ids:
        flash('No parts selected for listing.', 'warning')
        return redirect(url_for('atv.ebay_dashboard'))
    
    created_count = 0
    skipped_count = 0
    
    for part_id in part_ids:
        part = Part.query.get(part_id)
        
        if not part or not part.can_list_on_ebay():
            skipped_count += 1
            continue
        
        # Create title from ATV info and part name
        title = f"{part.atv.year} {part.atv.make} {part.atv.model} {part.name}"
        if len(title) > 80:
            title = title[:77] + "..."
        
        # Map condition
        condition = 'Used'
        if part.condition == 'new':
            condition = 'New'
        elif part.condition == 'used_poor':
            condition = 'For parts or not working'
        
        # Create eBay listing record
        listing = EbayListing(
            title=title,
            price=part.list_price or 0,
            status='pending',
            part_id=part.id,
            listing_data=json.dumps({
                'condition': condition,
                'description': part.description or '',
                'format': 'fixed_price',
                'duration': '30'
            })
        )
        
        # Update part status
        part.status = 'listed'
        part.platform = 'ebay'
        
        db.session.add(listing)
        created_count += 1
    
    db.session.commit()
    
    if created_count > 0:
        flash(f'Successfully created {created_count} eBay listings.', 'success')
    
    if skipped_count > 0:
        flash(f'Skipped {skipped_count} parts that were not eligible for listing.', 'warning')
    
    return redirect(url_for('atv.ebay_dashboard'))

@bp.route('/ebay/templates', methods=['GET'])
def ebay_templates():
    """Manage eBay listing templates"""
    templates = EbayTemplate.query.all()
    return render_template('atv/ebay/templates.html',
                          title='eBay Templates',
                          templates=templates)

@bp.route('/ebay/analytics', methods=['GET'])
def ebay_analytics():
    """View eBay sales analytics"""
    # Get monthly sales data
    now = datetime.now()
    current_year = now.year
    
    # Get month names
    month_names = list(calendar.month_name)[1:]
    
    # Initialize monthly data
    monthly_data = {month: {'count': 0, 'revenue': 0, 'profit': 0} for month in range(1, 13)}
    
    # Get all sold listings for current year
    sold_listings = EbayListing.query.filter(
        EbayListing.status == 'sold',
        db.extract('year', EbayListing.updated_at) == current_year
    ).all()
    
    # Populate monthly data
    for listing in sold_listings:
        part = Part.query.get(listing.part_id)
        if not part or not part.sold_price:
            continue
            
        month = listing.updated_at.month
        monthly_data[month]['count'] += 1
        monthly_data[month]['revenue'] += part.sold_price
        monthly_data[month]['profit'] += part.net_profit()
    
    # Format for chart.js
    monthly_counts = [monthly_data[m]['count'] for m in range(1, 13)]
    monthly_revenue = [monthly_data[m]['revenue'] for m in range(1, 13)]
    monthly_profit = [monthly_data[m]['profit'] for m in range(1, 13)]
    
    # Get top selling parts
    top_parts = db.session.query(
        Part.name, db.func.count(EbayListing.id).label('count')
    ).join(EbayListing).filter(
        EbayListing.status == 'sold'
    ).group_by(Part.name).order_by(db.desc('count')).limit(5).all()
    
    return render_template('atv/ebay/analytics.html',
                          title='eBay Analytics',
                          month_names=month_names,
                          monthly_counts=monthly_counts,
                          monthly_revenue=monthly_revenue,
                          monthly_profit=monthly_profit,
                          top_parts=top_parts)

@bp.route('/ebay/sync', methods=['POST'])
def sync_ebay_listings():
    """Sync listings with eBay API"""
    try:
        # This will be implemented when eBay API integration is ready
        # For now, we'll just return a success message
        return jsonify({'success': True, 'message': 'Synchronization not implemented yet.'})
    except Exception as e:
        logging.error(f"Error syncing eBay listings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/part/<int:part_id>/ebay/create', methods=['GET', 'POST'])
def create_ebay_listing(part_id):
    """Create a new eBay listing for a part"""
    part = Part.query.get_or_404(part_id)
    
    # If part is already listed, redirect to edit
    if part.status == 'listed' and part.platform == 'ebay':
        flash('This part is already listed on eBay. You can edit the existing listing.', 'info')
        existing_listing = EbayListing.query.filter_by(part_id=part.id).first()
        if existing_listing:
            return redirect(url_for('atv.edit_ebay_listing', listing_id=existing_listing.id))
    
    form = EbayListingForm()
    
    # Pre-populate with part info
    if request.method == 'GET':
        form.title.data = f"{part.atv.year} {part.atv.make} {part.atv.model} {part.name}"
        if len(form.title.data) > 80:
            form.title.data = form.title.data[:77] + "..."
        
        # Map part condition to eBay condition
        if part.condition == 'new':
            form.condition.data = 'New'
        elif part.condition == 'used_good':
            form.condition.data = 'Used'
        elif part.condition == 'used_fair':
            form.condition.data = 'Used'
        elif part.condition == 'used_poor':
            form.condition.data = 'For parts or not working'
        
        form.price.data = part.list_price
        form.description.data = part.description
    
    if form.validate_on_submit():
        # Create eBay listing record
        listing = EbayListing(
            title=form.title.data,
            price=form.price.data,
            status='pending',  # Will be 'active' after API integration
            part_id=part.id
        )
        
        # Update part status
        part.status = 'listed'
        part.platform = 'ebay'
        part.list_price = form.price.data
        
        # Store listing details (for future API integration)
        ebay_data = {
            'title': form.title.data,
            'condition': form.condition.data,
            'condition_description': form.condition_description.data,
            'format': form.format.data,
            'price': form.price.data,
            'reserve_price': form.reserve_price.data,
            'duration': form.duration.data,
            'category': form.category.data,
            'description': form.description.data,
            'shipping_cost': form.shipping_cost.data,
            'handling_time': form.handling_time.data,
            'return_policy': form.return_policy.data,
            'free_shipping': form.free_shipping.data,
            'calculated_shipping': form.calculated_shipping.data,
            'package_weight': form.package_weight.data,
            'package_dimensions': form.package_dimensions.data
        }
        
        # When we add API integration, we'll use this data to create the eBay listing
        
        db.session.add(listing)
        db.session.commit()
        
        flash('eBay listing created successfully! (Note: API integration pending)', 'success')
        return redirect(url_for('atv.view_part', id=part.id))
    
    return render_template('atv/ebay/create_listing.html', 
                          title='Create eBay Listing',
                          form=form, 
                          part=part)

@bp.route('/ebay/listing/<int:listing_id>/edit', methods=['GET', 'POST'])
def edit_ebay_listing(listing_id):
    """Edit an existing eBay listing"""
    listing = EbayListing.query.get_or_404(listing_id)
    part = Part.query.get_or_404(listing.part_id)
    form = EbayListingForm()
    
    if request.method == 'GET':
        form.title.data = listing.title
        form.price.data = listing.price
        # Other fields would be populated from stored data
    
    if form.validate_on_submit():
        # Update listing details
        listing.title = form.title.data
        listing.price = form.price.data
        
        # Update part info
        part.list_price = form.price.data
        
        db.session.commit()
        
        flash('eBay listing updated successfully!', 'success')
        return redirect(url_for('atv.view_part', id=part.id))
    
    return render_template('atv/ebay/edit_listing.html',
                          title='Edit eBay Listing',
                          form=form,
                          listing=listing,
                          part=part)

@bp.route('/ebay/listing/<int:listing_id>/end', methods=['POST'])
def end_ebay_listing(listing_id):
    """End an eBay listing and mark part as in stock"""
    listing = EbayListing.query.get_or_404(listing_id)
    part = Part.query.get(listing.part_id)
    
    if part:
        part.status = 'in_stock'
        part.platform = None
        part.listing_url = None
    
    listing.status = 'ended'
    db.session.commit()
    
    flash('eBay listing ended successfully!', 'success')
    return redirect(url_for('atv.view_part', id=part.id))

@bp.route('/ebay/listing/<int:listing_id>/sold', methods=['GET', 'POST'])
def mark_listing_sold(listing_id):
    """Mark an eBay listing as sold and collect sale details"""
    listing = EbayListing.query.get_or_404(listing_id)
    part = Part.query.get_or_404(listing.part_id)
    
    if request.method == 'POST':
        sold_price = float(request.form.get('sold_price', 0))
        shipping_cost = float(request.form.get('shipping_cost', 0))
        platform_fees = float(request.form.get('platform_fees', 0))
        
        # Update part status
        part.status = 'sold'
        part.sold_price = sold_price
        part.shipping_cost = shipping_cost
        part.platform_fees = platform_fees
        part.sold_date = datetime.now()
        
        # Update listing status
        listing.status = 'sold'
        
        # Calculate profit and update ATV earnings
        profit = sold_price - (part.source_price or 0) - shipping_cost - platform_fees
        part.atv.total_earnings = (part.atv.total_earnings or 0) + profit
        
        db.session.commit()
        
        flash('Part marked as sold successfully!', 'success')
        return redirect(url_for('atv.view_part', id=part.id))
    
    return render_template('atv/ebay/mark_sold.html',
                          title='Mark eBay Listing as Sold',
                          listing=listing,
                          part=part)
