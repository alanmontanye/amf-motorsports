"""Admin routes for data management"""
from flask import render_template, redirect, url_for, flash, send_file, request
from app.admin import bp
from app.utils.data_management import export_data, import_data
import os
from datetime import datetime
from werkzeug.utils import secure_filename

@bp.route('/admin')
def index():
    """Admin dashboard"""
    # Get list of existing backups
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    backups = []
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.json'):
                path = os.path.join(backup_dir, file)
                backups.append({
                    'filename': file,
                    'size': os.path.getsize(path) / 1024,  # Size in KB
                    'modified': datetime.fromtimestamp(os.path.getmtime(path))
                })
    backups.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('admin/index.html', backups=backups)

@bp.route('/admin/backup')
def create_backup():
    """Create a new backup"""
    try:
        backup_path = export_data()
        flash(f'Backup created successfully: {os.path.basename(backup_path)}', 'success')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

@bp.route('/admin/restore/<filename>')
def restore_backup(filename):
    """Restore from a backup file"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
        backup_path = os.path.join(backup_dir, secure_filename(filename))
        
        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('admin.index'))
        
        import_data(backup_path, clear_existing=True)
        flash('Data restored successfully!', 'success')
    except Exception as e:
        flash(f'Error restoring backup: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

@bp.route('/admin/download/<filename>')
def download_backup(filename):
    """Download a backup file"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
        return send_file(
            os.path.join(backup_dir, secure_filename(filename)),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error downloading backup: {str(e)}', 'error')
        return redirect(url_for('admin.index'))

@bp.route('/admin/delete/<filename>')
def delete_backup(filename):
    """Delete a backup file"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
        os.remove(os.path.join(backup_dir, secure_filename(filename)))
        flash('Backup deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting backup: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))

@bp.route('/admin/upload', methods=['POST'])
def upload_backup():
    """Upload a backup file"""
    if 'backup' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('admin.index'))
    
    file = request.files['backup']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin.index'))
    
    if not file.filename.endswith('.json'):
        flash('Invalid file type. Please upload a .json backup file', 'error')
        return redirect(url_for('admin.index'))
    
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        file.save(os.path.join(backup_dir, filename))
        flash('Backup uploaded successfully', 'success')
    except Exception as e:
        flash(f'Error uploading backup: {str(e)}', 'error')
    
    return redirect(url_for('admin.index'))
