"""eBay integration routes for OAuth and API functionality"""
from flask import render_template, redirect, url_for, flash, request, session, jsonify, current_app
from app.atv import bp
from app.models import Part, EbayListing, EbayCredentials, Image, ATV, EbayOrder, EbayOrderItem
from app.atv.ebay_forms import EbayListingForm
from app.atv.ebay_api import EbayAPI
from app import db
from datetime import datetime
import json
import logging

# Configuration
EBAY_REDIRECT_URI = "/atv/ebay/auth/callback"  # Will be expanded to full URL in the authorize route

@bp.route('/ebay/settings', methods=['GET', 'POST'])
def ebay_settings():
    """Manage eBay API settings"""
    # Get existing credentials if any
    credentials = EbayCredentials.query.first()
    
    if request.method == 'POST':
        # Handle form submission
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
        environment = request.form.get('environment', 'sandbox')
        
        if not credentials:
            credentials = EbayCredentials()
        
        credentials.client_id = client_id
        credentials.client_secret = client_secret
        credentials.environment = environment
        
        # Save default policies
        credentials.default_return_policy = request.form.get('return_policy', '30_days')
        credentials.default_shipping_policy = request.form.get('shipping_policy', 'calculated')
        credentials.default_payment_policy = request.form.get('payment_policy', 'immediate')
        
        db.session.add(credentials)
        db.session.commit()
        
        flash('eBay settings updated successfully!', 'success')
        return redirect(url_for('atv.ebay_dashboard'))
    
    return render_template('atv/ebay/settings.html',
                          title='eBay Settings',
                          credentials=credentials)

@bp.route('/ebay/auth/authorize')
def ebay_authorize():
    """Redirect user to eBay for authorization"""
    try:
        # Get full redirect URI including domain
        redirect_uri = request.host_url.rstrip('/') + EBAY_REDIRECT_URI
        
        # Create eBay API instance
        ebay_api = EbayAPI()
        
        # Get authorization URL
        auth_url = ebay_api.get_auth_url(redirect_uri)
        
        # Redirect user to eBay for authorization
        return redirect(auth_url)
    except Exception as e:
        flash(f'Error initiating eBay authorization: {str(e)}', 'error')
        return redirect(url_for('atv.ebay_settings'))

@bp.route('/ebay/auth/callback')
def ebay_callback():
    """Handle OAuth callback from eBay"""
    # Check for error
    if 'error' in request.args:
        flash(f"eBay authorization error: {request.args.get('error')}", 'error')
        return redirect(url_for('atv.ebay_settings'))
    
    # Get authorization code
    auth_code = request.args.get('code')
    if not auth_code:
        flash('No authorization code received from eBay', 'error')
        return redirect(url_for('atv.ebay_settings'))
    
    try:
        # Get full redirect URI including domain
        redirect_uri = request.host_url.rstrip('/') + EBAY_REDIRECT_URI
        
        # Exchange code for token
        ebay_api = EbayAPI()
        token_data = ebay_api.get_access_token(auth_code, redirect_uri)
        
        flash('eBay authorization successful! Your account is now connected.', 'success')
        return redirect(url_for('atv.ebay_dashboard'))
    except Exception as e:
        flash(f'Error during eBay authorization: {str(e)}', 'error')
        return redirect(url_for('atv.ebay_settings'))

@bp.route('/ebay/auth/refresh')
def ebay_refresh_token():
    """Manually refresh eBay token"""
    try:
        ebay_api = EbayAPI()
        ebay_api.refresh_token_if_needed()
        flash('eBay token refreshed successfully!', 'success')
    except Exception as e:
        flash(f'Error refreshing eBay token: {str(e)}', 'error')
    
    return redirect(url_for('atv.ebay_settings'))

@bp.route('/ebay/part/<int:part_id>/list', methods=['POST'])
def list_part_on_ebay(part_id):
    """List a part on eBay using the API"""
    try:
        ebay_api = EbayAPI()
        listing = ebay_api.list_part(part_id)
        flash(f'Successfully listed part on eBay! Listing ID: {listing.ebay_item_id}', 'success')
    except Exception as e:
        flash(f'Error listing part on eBay: {str(e)}', 'error')
    
    return redirect(url_for('atv.view_part', id=part_id))

@bp.route('/ebay/sync-orders')
def sync_ebay_orders():
    """Synchronize orders from eBay"""
    try:
        ebay_api = EbayAPI()
        updated_count = ebay_api.sync_orders()
        
        if updated_count > 0:
            flash(f'Successfully synchronized {updated_count} orders from eBay!', 'success')
        else:
            flash('No new eBay orders to synchronize.', 'info')
    except Exception as e:
        flash(f'Error synchronizing eBay orders: {str(e)}', 'error')
    
    return redirect(url_for('atv.ebay_dashboard'))

@bp.route('/ebay/part/<int:part_id>/analyze-price')
def analyze_part_price(part_id):
    """Analyze and suggest price for a part based on eBay data"""
    try:
        ebay_api = EbayAPI()
        price_data = ebay_api.analyze_price(part_id)
        
        if price_data['success']:
            return render_template('atv/ebay/price_analysis.html',
                                 title='Price Analysis',
                                 price_data=price_data,
                                 part_id=part_id)
        else:
            flash(price_data['message'], 'warning')
            return redirect(url_for('atv.view_part', id=part_id))
    except Exception as e:
        flash(f'Error analyzing price: {str(e)}', 'error')
        return redirect(url_for('atv.view_part', id=part_id))

@bp.route('/ebay/api/price-suggestion')
def price_suggestion_api():
    """API endpoint for getting price suggestions while creating/editing parts"""
    try:
        # Get parameters from request
        atv_id = request.args.get('atv_id', type=int)
        part_name = request.args.get('part_name')
        part_id = request.args.get('part_id', type=int)
        
        # Validate parameters
        if not part_name and not part_id:
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400
        
        ebay_api = EbayAPI()
        
        # If we have a part_id, analyze that directly
        if part_id:
            price_data = ebay_api.analyze_price(part_id)
            return jsonify(price_data)
        
        # Otherwise, we need to create a temporary part for analysis
        atv = ATV.query.get_or_404(atv_id)
        
        # Create a temporary part object (not saved to DB)
        temp_part = Part(
            name=part_name,
            atv=atv,
            atv_id=atv_id
        )
        
        # Try to analyze the temporary part
        similar_items = ebay_api.find_similar_items(temp_part)
        
        # Extract prices
        sold_prices = [item['price'] for item in similar_items['sold'] if 'price' in item]
        active_prices = [item['price'] for item in similar_items['active'] if 'price' in item]
        
        if not sold_prices and not active_prices:
            return jsonify({
                'success': False,
                'message': 'No similar items found for price analysis'
            })
        
        # Calculate statistics
        result = {
            'success': True,
            'part_name': part_name
        }
        
        if sold_prices:
            result['sold_count'] = len(sold_prices)
            result['sold_min'] = min(sold_prices)
            result['sold_max'] = max(sold_prices)
            result['sold_avg'] = sum(sold_prices) / len(sold_prices)
        
        if active_prices:
            result['active_count'] = len(active_prices)
            result['active_min'] = min(active_prices)
            result['active_max'] = max(active_prices)
            result['active_avg'] = sum(active_prices) / len(active_prices)
        
        # Generate suggested price
        if sold_prices:
            # Weight more heavily towards sold items if available
            suggested_price = result['sold_avg'] * 0.7
            if active_prices:
                suggested_price += result['active_avg'] * 0.3
        elif active_prices:
            # If only active listings are available, use a slight discount
            suggested_price = result['active_avg'] * 0.95
        else:
            suggested_price = 0
        
        result['suggested_price'] = round(suggested_price, 2)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in price suggestion API: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/ebay/part/<int:part_id>/preview-description')
def preview_ai_description(part_id):
    """Preview AI-generated description for a part"""
    try:
        part = Part.query.get_or_404(part_id)
        
        ebay_api = EbayAPI()
        description = ebay_api._generate_listing_description(part)
        
        return render_template('atv/ebay/preview_description.html',
                             title='Preview eBay Description',
                             description=description,
                             part=part)
    except Exception as e:
        flash(f'Error generating description preview: {str(e)}', 'error')
        return redirect(url_for('atv.view_part', id=part_id))

@bp.route('/ebay/part/<int:part_id>/apply-description', methods=['POST'])
def apply_ai_description(part_id):
    """Apply an AI-generated description to a part"""
    try:
        part = Part.query.get_or_404(part_id)
        description = request.form.get('description')
        
        if description:
            # Only update the description, don't change any other fields
            part.description = description
            db.session.commit()
            flash('AI-generated description applied successfully!', 'success')
        else:
            flash('No description provided.', 'warning')
            
        return redirect(url_for('atv.view_part', id=part_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error applying description: {str(e)}', 'error')
        return redirect(url_for('atv.view_part', id=part_id))

@bp.route('/ebay/part/<int:part_id>/regenerate-description')
def regenerate_description(part_id):
    """Generate a new AI description for a part"""
    try:
        ebay_api = EbayAPI()
        return redirect(url_for('atv.preview_ai_description', part_id=part_id, refresh=True))
    except Exception as e:
        flash(f'Error regenerating description: {str(e)}', 'error')
        return redirect(url_for('atv.view_part', id=part_id))

@bp.route('/ebay/part/<int:part_id>/update-price', methods=['POST'])
def update_part_price(part_id):
    """Update a part's price based on eBay market analysis"""
    try:
        part = Part.query.get_or_404(part_id)
        price = request.form.get('price')
        
        if price:
            # Parse and validate the price
            try:
                price_float = float(price)
                if price_float <= 0:
                    raise ValueError("Price must be greater than zero")
                
                # Only update the price, don't change any other fields
                part.list_price = price_float
                db.session.commit()
                
                flash(f'Price updated to ${price_float:.2f} based on eBay market analysis!', 'success')
            except ValueError as ve:
                flash(f'Invalid price value: {str(ve)}', 'error')
        else:
            flash('No price provided.', 'warning')
            
        return redirect(url_for('atv.view_part', id=part_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating price: {str(e)}', 'error')
        return redirect(url_for('atv.view_part', id=part_id))

@bp.route('/ebay/bulk-list', methods=['POST'])
def bulk_list_on_ebay():
    """Create eBay listings for multiple parts at once"""
    part_ids = request.form.getlist('part_ids')
    use_price_analysis = request.form.get('use_price_analysis') == 'on'
    
    if not part_ids:
        flash('No parts selected for listing.', 'warning')
        return redirect(url_for('atv.ebay_dashboard'))
    
    created_count = 0
    priced_count = 0
    skipped_count = 0
    error_count = 0
    
    ebay_api = EbayAPI()
    
    for part_id in part_ids:
        try:
            part = Part.query.get(part_id)
            
            if not part or not part.can_list_on_ebay():
                skipped_count += 1
                continue
            
            # Auto-adjust price if requested
            if use_price_analysis and ebay_api.credentials and ebay_api.credentials.is_active:
                try:
                    price_data = ebay_api.analyze_price(part.id)
                    if price_data.get('success') and price_data.get('suggested_price'):
                        # Only update if we have a valid suggested price
                        part.list_price = price_data.get('suggested_price')
                        db.session.add(part)
                        db.session.commit()
                        priced_count += 1
                except Exception as e:
                    logging.warning(f"Price analysis failed for part {part.id}: {str(e)}")
            
            # Create listing
            ebay_api.list_part(part.id)
            created_count += 1
            
        except Exception as e:
            logging.error(f"Error listing part {part_id} on eBay: {str(e)}")
            error_count += 1
    
    if created_count > 0:
        flash(f'Successfully created {created_count} eBay listings.', 'success')
    
    if priced_count > 0:
        flash(f'Updated prices for {priced_count} parts based on eBay market analysis.', 'info')
    
    if skipped_count > 0:
        flash(f'Skipped {skipped_count} parts that were not eligible for listing.', 'warning')
    
    if error_count > 0:
        flash(f'Failed to list {error_count} parts due to errors. Check the logs for details.', 'error')
    
    return redirect(url_for('atv.ebay_dashboard'))

@bp.route('/ebay/order/<int:order_id>')
def view_order(order_id):
    """View details of an eBay order"""
    try:
        # Get order with items
        order = EbayOrder.query.get_or_404(order_id)
        order_items = EbayOrderItem.query.filter_by(order_id=order_id).all()
        
        return render_template('atv/ebay/view_order.html',
                             title='eBay Order Details',
                             order=order,
                             order_items=order_items)
    except Exception as e:
        flash(f'Error viewing order: {str(e)}', 'error')
        return redirect(url_for('atv.ebay_dashboard'))

@bp.route('/ebay/order/<int:order_id>/mark-shipped', methods=['POST'])
def mark_shipped(order_id):
    """Mark an eBay order as shipped"""
    try:
        order = EbayOrder.query.get_or_404(order_id)
        
        # Get form data
        tracking_number = request.form.get('tracking_number')
        carrier = request.form.get('carrier')
        
        if not tracking_number or not carrier:
            flash('Tracking number and carrier are required.', 'warning')
            return redirect(url_for('atv.view_order', order_id=order_id))
        
        # Update order status
        order.status = 'SHIPPED'
        order.tracking_number = tracking_number
        order.carrier = carrier
        order.shipped_date = datetime.utcnow()
        
        db.session.commit()
        
        # Update shipping status on eBay
        try:
            ebay_api = EbayAPI()
            ebay_api.update_tracking_info(order.ebay_order_id, tracking_number, carrier)
            flash('Order marked as shipped and tracking information sent to eBay!', 'success')
        except Exception as api_error:
            # Log the API error but still continue (the database update was successful)
            logging.error(f"Error updating tracking on eBay: {str(api_error)}")
            flash('Order marked as shipped in the database, but there was an error sending tracking to eBay.', 'warning')
        
        return redirect(url_for('atv.view_order', order_id=order_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order: {str(e)}', 'error')
        return redirect(url_for('atv.view_order', order_id=order_id))
