"""
eBay Analytics Module

This module provides functionality for analyzing eBay market data, 
generating price recommendations, and tracking selling performance.
"""
from flask import render_template, jsonify, request
from app.atv import bp
from app.models import Part, EbayListing, EbayHistoricalPrice
from app import db
from datetime import datetime, timedelta
import json

@bp.route('/ebay/analytics', methods=['GET'])
def ebay_analytics_dashboard():
    """eBay analytics dashboard showing performance metrics"""
    # This is a placeholder and will be implemented with real data later
    return render_template('atv/ebay_analytics.html')

@bp.route('/ebay/analytics/pricing', methods=['GET'])
def pricing_analytics():
    """View historical pricing data and get recommendations"""
    return render_template('atv/ebay_pricing.html')

@bp.route('/api/ebay/price-recommendation/<int:part_id>', methods=['GET'])
def get_price_recommendation(part_id):
    """API endpoint to get price recommendations for a part"""
    part = Part.query.get_or_404(part_id)
    
    # Import here to avoid circular imports
    from app.atv.ebay_api import EbayAnalyticsManager
    
    # Get recommendation from the API manager
    recommendation = EbayAnalyticsManager.get_price_recommendation(part)
    
    return jsonify(recommendation)

@bp.route('/api/ebay/similar-sold/<int:part_id>', methods=['GET'])
def get_similar_sold_items(part_id):
    """API endpoint to get similar sold items for a part"""
    part = Part.query.get_or_404(part_id)
    
    # Import here to avoid circular imports
    from app.atv.ebay_api import EbayAnalyticsManager
    
    # Generate search keywords based on part
    keywords = f"{part.atv.year} {part.atv.make} {part.atv.model} {part.name}"
    
    # Map condition
    condition_map = {
        'new': 'New',
        'used_good': 'Used',
        'used_fair': 'Used',
        'used_poor': 'For parts or not working'
    }
    condition = condition_map.get(part.condition, 'Used')
    
    # Get similar items from the API manager
    result = EbayAnalyticsManager.get_similar_sold_items(keywords, condition)
    
    # Store the results for future reference
    if result.get('success') and result.get('items'):
        for item in result.get('items', []):
            # Check if we already have this item
            existing = EbayHistoricalPrice.query.filter_by(
                ebay_item_id=item.get('item_id')
            ).first()
            
            if not existing:
                price_record = EbayHistoricalPrice(
                    keywords=keywords,
                    part_id=part.id,
                    title=item.get('title'),
                    sold_price=item.get('price'),
                    shipping_cost=item.get('shipping', 0),
                    total_price=item.get('price') + item.get('shipping', 0),
                    sold_date=item.get('sold_date'),
                    condition=item.get('condition'),
                    ebay_item_id=item.get('item_id')
                )
                db.session.add(price_record)
        
        db.session.commit()
    
    return jsonify(result)

@bp.route('/ebay/analytics/part/<int:part_id>', methods=['GET'])
def part_price_analysis(part_id):
    """View price analysis for a specific part"""
    part = Part.query.get_or_404(part_id)
    
    # Get historical price data for this part
    historical_data = EbayHistoricalPrice.query.filter_by(
        part_id=part.id
    ).order_by(EbayHistoricalPrice.sold_date.desc()).all()
    
    # Import here to avoid circular imports
    from app.atv.ebay_api import EbayAnalyticsManager
    
    # Get recommendation
    recommendation = EbayAnalyticsManager.get_price_recommendation(part)
    
    return render_template(
        'atv/part_price_analysis.html',
        part=part,
        historical_data=historical_data,
        recommendation=recommendation
    )

@bp.route('/api/ebay/analytics/performance', methods=['GET'])
def get_performance_metrics():
    """API endpoint to get selling performance metrics"""
    # Define timeframe - default to last 30 days
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Count sold listings
    sold_listings = EbayListing.query.filter(
        EbayListing.status == 'sold',
        EbayListing.updated_at >= start_date
    ).count()
    
    # Count active listings
    active_listings = EbayListing.query.filter(
        EbayListing.status == 'active'
    ).count()
    
    # Calculate average sale price and time to sell (placeholder data)
    # Will be replaced with actual calculations when more data is available
    metrics = {
        'sold_count': sold_listings,
        'active_count': active_listings,
        'avg_sale_price': 75.50,  # Placeholder
        'avg_days_to_sell': 5.2,  # Placeholder
        'success_rate': 85 if sold_listings > 0 else 0  # Placeholder
    }
    
    return jsonify(metrics)
