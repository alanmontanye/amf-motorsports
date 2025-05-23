"""eBay dashboard route and supporting functions"""
from flask import render_template, flash, current_app
from app.atv import bp
from app.models import Part, EbayListing, EbayOrder, EbayCredentials
from app.atv.ebay_api import EbayAPI
from sqlalchemy import func
from datetime import datetime, timedelta

@bp.route('/ebay/dashboard')
def ebay_dashboard():
    """eBay integration dashboard"""
    try:
        # Check if we have eBay credentials
        credentials = EbayCredentials.query.first()
        ebay_connected = credentials is not None and credentials.is_active
        
        # Get active eBay listings
        active_listings = []
        if ebay_connected:
            active_listings = EbayListing.query.filter(
                EbayListing.status.in_(['active', 'pending'])
            ).order_by(EbayListing.created_at.desc()).all()
        
        # Get parts eligible for eBay listing
        eligible_parts = Part.query.filter(
            Part.status == 'available',
            Part.list_price > 0,
            Part.condition.in_(['new', 'used_good', 'used_fair'])
        ).all()
        
        # Get recent eBay orders 
        recent_orders = []
        if ebay_connected:
            recent_orders = EbayOrder.query.order_by(EbayOrder.order_date.desc()).limit(30).all()
        
        # Get order statistics
        total_revenue = 0
        awaiting_shipment = 0
        shipped_orders = 0
        
        if recent_orders:
            # Calculate total revenue
            total_revenue = sum(order.total_price for order in recent_orders)
            
            # Count orders by status
            for order in recent_orders:
                if order.status == 'AWAITING_SHIPMENT':
                    awaiting_shipment += 1
                elif order.status == 'SHIPPED':
                    shipped_orders += 1
        
        # Get all ATVs for filter dropdown
        from app.models import ATV
        atvs = ATV.query.filter(ATV.status != 'deleted').order_by(ATV.year.desc(), ATV.make, ATV.model).all()
        
        # Filter parts by ATV if specified
        atv_id = request.args.get('atv_id', type=int)
        if atv_id:
            eligible_parts = [p for p in eligible_parts if p.atv_id == atv_id]
        
        return render_template('atv/ebay/dashboard.html',
                             title='eBay Dashboard',
                             ebay_connected=ebay_connected,
                             active_listings=active_listings,
                             eligible_parts=eligible_parts,
                             recent_orders=recent_orders,
                             total_revenue=total_revenue,
                             awaiting_shipment=awaiting_shipment,
                             shipped_orders=shipped_orders,
                             atvs=atvs)
    except Exception as e:
        current_app.logger.error(f"Error in eBay dashboard: {str(e)}")
        flash(f"Error loading eBay dashboard: {str(e)}", "error")
        return render_template('atv/ebay/dashboard.html',
                             title='eBay Dashboard',
                             ebay_connected=False,
                             active_listings=[],
                             eligible_parts=[],
                             recent_orders=[],
                             total_revenue=0,
                             awaiting_shipment=0,
                             shipped_orders=0,
                             atvs=[],
                             error=str(e))
