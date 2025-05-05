from flask import render_template, redirect, url_for, request, jsonify
from app.atv import bp
from app.models import Storage, Part
from app import db

@bp.route('/storage')
def storage_list():
    """List all storage locations"""
    storages = Storage.query.order_by(Storage.name).all()
    return render_template('atv/storage/index.html', 
                         title='Storage Locations',
                         storages=storages)

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
