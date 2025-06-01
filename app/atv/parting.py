from flask import Blueprint, request, flash, redirect, url_for, jsonify, render_template
from flask_login import login_required, current_user
from app import db
from app.models import ATV, Part
from app.utils import admin_required
import uuid

parting_bp = Blueprint('parting', __name__)

@parting_bp.route('/change_parting_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def change_parting_status(id):
    """Change the parting status of an ATV"""
    atv = ATV.query.get_or_404(id)
    new_status = request.form.get('parting_status')
    
    if new_status not in ['whole', 'parting_out', 'parted_out']:
        flash('Invalid parting status', 'danger')
        return redirect(url_for('atv.view_atv', id=id))
    
    # If this is the first time parting an ATV, generate a machine_id if needed
    if atv.parting_status == 'whole' and new_status != 'whole' and not atv.machine_id:
        atv.machine_id = str(uuid.uuid4())
    
    # Update the parting status
    atv.parting_status = new_status
    
    # If status is being set to parted_out, check if there are any parts
    if new_status == 'parted_out':
        parts_count = Part.query.filter_by(atv_id=id).count()
        if parts_count == 0:
            flash('Cannot mark as fully parted out: no parts have been added yet', 'warning')
            return redirect(url_for('atv.view_atv', id=id))
    
    db.session.commit()
    
    flash(f'ATV parting status updated to {new_status.replace("_", " ").title()}', 'success')
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True)
    
    # Redirect back to appropriate page
    if request.referrer and 'index' in request.referrer:
        return redirect(url_for('atv.index'))
    else:
        return redirect(url_for('atv.view_atv', id=id))


@parting_bp.route('/parting_dashboard')
@login_required
def parting_dashboard():
    """Dashboard showing ATVs in various parting stages"""
    parting_out_atvs = ATV.query.filter_by(parting_status='parting_out').all()
    recently_parted = ATV.query.filter_by(parting_status='parted_out').order_by(ATV.id.desc()).limit(5).all()
    
    # Get counts for dashboard stats
    whole_count = ATV.query.filter_by(parting_status='whole').count()
    parting_count = ATV.query.filter_by(parting_status='parting_out').count()
    parted_count = ATV.query.filter_by(parting_status='parted_out').count()
    
    # Get part counts by status
    in_stock_parts = Part.query.filter_by(status='in_stock').count()
    sold_parts = Part.query.filter_by(status='sold').count()
    listed_parts = Part.query.filter_by(status='listed').count()
    
    # Get ATVs with most parts
    top_atv_parts = db.session.query(
        ATV, db.func.count(Part.id).label('parts_count')
    ).join(Part).group_by(ATV.id).order_by(db.desc('parts_count')).limit(5).all()
    
    return render_template('atv/parting/dashboard.html',
        title='Parting Dashboard',
        parting_out_atvs=parting_out_atvs,
        recently_parted=recently_parted,
        whole_count=whole_count,
        parting_count=parting_count,
        parted_count=parted_count,
        in_stock_parts=in_stock_parts,
        sold_parts=sold_parts,
        listed_parts=listed_parts,
        top_atv_parts=top_atv_parts
    )
