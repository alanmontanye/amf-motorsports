"""
eBay Settings Module

This module handles configuration and settings for eBay integration.
It provides forms and routes for managing eBay credentials and preferences.
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from app.atv import bp
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, URL
from app import db
from app.models import EbayCredentials, EbayTemplate

class EbaySettingsForm(FlaskForm):
    """Form for managing eBay API credentials and settings"""
    environment = SelectField('Environment', choices=[
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production (Live)')
    ])
    
    client_id = StringField('Client ID', validators=[DataRequired(), Length(max=256)])
    client_secret = PasswordField('Client Secret', validators=[DataRequired(), Length(max=256)])
    
    default_return_policy = SelectField('Default Return Policy', choices=[
        ('no_returns', 'No Returns'),
        ('30_days', '30 Day Returns'),
        ('60_days', '60 Day Returns')
    ])
    
    default_shipping_policy = SelectField('Default Shipping Policy', choices=[
        ('free', 'Free Shipping'),
        ('flat', 'Flat Rate'),
        ('calculated', 'Calculated Shipping')
    ])
    
    default_payment_policy = SelectField('Default Payment Policy', choices=[
        ('immediate', 'Immediate Payment Required'),
        ('paypal', 'PayPal Accepted'),
        ('any', 'Any Payment Method')
    ])
    
    is_active = BooleanField('Enable eBay Integration')

@bp.route('/ebay/settings', methods=['GET', 'POST'])
def ebay_settings():
    """Manage eBay integration settings"""
    # Get or create settings
    settings = EbayCredentials.query.first()
    if not settings:
        settings = EbayCredentials()
        db.session.add(settings)
        db.session.commit()
    
    form = EbaySettingsForm()
    
    # Populate form with existing data
    if request.method == 'GET':
        form.environment.data = settings.environment
        form.client_id.data = settings.client_id
        # Don't populate client_secret for security
        form.default_return_policy.data = settings.default_return_policy
        form.default_shipping_policy.data = settings.default_shipping_policy
        form.default_payment_policy.data = settings.default_payment_policy
        form.is_active.data = settings.is_active
    
    # Process form submission
    if form.validate_on_submit():
        settings.environment = form.environment.data
        settings.client_id = form.client_id.data
        
        # Only update client secret if provided
        if form.client_secret.data:
            settings.client_secret = form.client_secret.data
            
        settings.default_return_policy = form.default_return_policy.data
        settings.default_shipping_policy = form.default_shipping_policy.data
        settings.default_payment_policy = form.default_payment_policy.data
        settings.is_active = form.is_active.data
        
        db.session.commit()
        flash('eBay settings updated successfully', 'success')
        return redirect(url_for('atv.ebay_settings'))
    
    # If integration is active and we have credentials, show authorization link
    auth_link = None
    if settings.client_id and settings.is_active:
        from app.atv.ebay_api import EbayAuthManager
        auth_link = EbayAuthManager.get_auth_url()
    
    return render_template(
        'atv/ebay_settings.html',
        form=form,
        settings=settings,
        auth_link=auth_link
    )

@bp.route('/ebay/authorize', methods=['GET'])
def ebay_authorize():
    """Handle eBay authorization callback"""
    # This route will be called by eBay after user authorizes the app
    code = request.args.get('code')
    if not code:
        flash('Authorization failed: No code received', 'danger')
        return redirect(url_for('atv.ebay_settings'))
    
    # Exchange code for tokens
    from app.atv.ebay_api import EbayAuthManager
    token_response = EbayAuthManager.exchange_code_for_token(code)
    
    if not token_response or 'access_token' not in token_response:
        flash('Failed to get access token', 'danger')
        return redirect(url_for('atv.ebay_settings'))
    
    # Save tokens to database
    settings = EbayCredentials.query.first()
    if not settings:
        flash('eBay settings not found', 'danger')
        return redirect(url_for('atv.ebay_settings'))
    
    # Update tokens
    settings.access_token = token_response['access_token']
    settings.refresh_token = token_response.get('refresh_token')
    
    # Calculate token expiry
    from datetime import datetime, timedelta
    expires_in = token_response.get('expires_in', 7200)
    settings.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    
    db.session.commit()
    flash('eBay authorization successful', 'success')
    return redirect(url_for('atv.ebay_settings'))

@bp.route('/ebay/templates', methods=['GET'])
def ebay_templates():
    """Manage eBay listing templates"""
    templates = EbayTemplate.query.all()
    return render_template('atv/ebay_templates.html', templates=templates)

@bp.route('/ebay/templates/create', methods=['GET', 'POST'])
def create_ebay_template():
    """Create a new eBay listing template"""
    # To be implemented
    flash('Template creation coming soon in future update', 'info')
    return redirect(url_for('atv.ebay_templates'))
