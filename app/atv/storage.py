from flask import render_template, redirect, url_for, request, jsonify, flash
from app.atv import bp
from app.models import Storage, Part
from app import db
from datetime import datetime

@bp.route('/storage')
def storage_list():
    """List all storage locations"""
    storages = Storage.query.order_by(Storage.name).all()
    
    # Get count of parts in each storage location
    storage_stats = {}
    for storage in storages:
        part_count = Part.query.filter_by(storage_id=storage.id).count()
        storage_stats[storage.id] = part_count
    
    return render_template('atv/storage/index.html', 
                          title='Storage Locations',
                          storages=storages,
                          storage_stats=storage_stats)

@bp.route('/storage/add', methods=['POST'])
def add_storage():
    """Add a new storage location"""
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
        
    # Check for duplicate names
    if Storage.query.filter_by(name=name).first():
        return jsonify({'error': 'Storage location with this name already exists'}), 400
    
    storage = Storage(name=name, description=description)
    db.session.add(storage)
    db.session.commit()
    
    return jsonify({
        'id': storage.id,
        'name': storage.name,
        'description': storage.description
    })

@bp.route('/storage/<int:id>/edit', methods=['POST'])
def edit_storage(id):
    """Edit a storage location"""
    storage = Storage.query.get_or_404(id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
        
    # Check for duplicate names, excluding current storage
    duplicate = Storage.query.filter(Storage.name == name, Storage.id != id).first()
    if duplicate:
        return jsonify({'error': 'Storage location with this name already exists'}), 400
    
    storage.name = name
    storage.description = description
    db.session.commit()
    
    return jsonify({
        'id': storage.id,
        'name': storage.name,
        'description': storage.description
    })

@bp.route('/storage/<int:id>/delete', methods=['POST'])
def delete_storage(id):
    """Delete a storage location"""
    storage = Storage.query.get_or_404(id)
    
    # Check if any parts are using this storage location
    if Part.query.filter_by(storage_id=id).first():
        return jsonify({'error': 'Cannot delete storage location that contains parts'}), 400
    
    db.session.delete(storage)
    db.session.commit()
    
    return jsonify({'message': 'Storage location deleted successfully'})

@bp.route('/storage/bulk-move', methods=['GET', 'POST'])
def bulk_move_storage():
    """Move all parts from one storage location to another"""
    # Get all storage locations for the form
    storages = Storage.query.order_by(Storage.name).all()
    
    if request.method == 'POST':
        source_id = request.form.get('source_id', type=int)
        destination_id = request.form.get('destination_id', type=int)
        
        # Validate inputs
        if not source_id or not destination_id:
            flash('Both source and destination storage locations are required.', 'error')
            return redirect(url_for('atv.bulk_move_storage'))
            
        if source_id == destination_id:
            flash('Source and destination cannot be the same.', 'error')
            return redirect(url_for('atv.bulk_move_storage'))
        
        # Get storage locations
        source = Storage.query.get_or_404(source_id)
        destination = Storage.query.get_or_404(destination_id)
        
        # Get all parts in the source location
        parts = Part.query.filter_by(storage_id=source_id).all()
        
        if not parts:
            flash(f'No parts found in {source.name}.', 'warning')
            return redirect(url_for('atv.bulk_move_storage'))
        
        # Move all parts to the destination
        part_count = 0
        for part in parts:
            part.storage_id = destination_id
            part.updated_at = datetime.utcnow()
            part_count += 1
        
        db.session.commit()
        
        flash(f'Successfully moved {part_count} parts from {source.name} to {destination.name}.', 'success')
        return redirect(url_for('atv.storage_list'))
    
    return render_template('atv/storage/bulk_move.html',
                          title='Bulk Move Parts',
                          storages=storages)
