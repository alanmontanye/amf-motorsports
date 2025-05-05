from flask import Blueprint, current_app, jsonify, request
import os
from app import db
from app.models import Storage, ATV

# Create a separate blueprint for initialization
init_bp = Blueprint('init', __name__)

@init_bp.route('/initialize-database', methods=['GET'])
def initialize_database():
    """Initialize the database with required tables and sample data"""
    # Only allow in production and with a secret key for security
    init_key = request.args.get('key')
    expected_key = os.environ.get('INIT_KEY')
    
    if not expected_key or init_key != expected_key:
        return jsonify({"error": "Unauthorized access"}), 401
    
    try:
        # Create all tables
        db.create_all()
        current_app.logger.info("All database tables created successfully!")
        
        # Check if Storage table has any entries
        if Storage.query.count() == 0:
            # Add basic storage locations
            storage_locations = [
                Storage(name="Main Garage", description="Primary workspace and storage"),
                Storage(name="Shed", description="Outdoor storage for larger parts"),
                Storage(name="Parts Cabinet", description="Organized shelving for small parts"),
                Storage(name="Offsite Storage", description="Rental unit for overflow")
            ]
            
            for storage in storage_locations:
                db.session.add(storage)
            
            db.session.commit()
            current_app.logger.info(f"Added {len(storage_locations)} sample storage locations")
        
        return jsonify({
            "success": True,
            "message": "Database initialized successfully",
            "tables_count": len(db.metadata.tables),
            "storage_count": Storage.query.count(),
            "atv_count": ATV.query.count()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error initializing database: {str(e)}")
        return jsonify({"error": str(e)}), 500
