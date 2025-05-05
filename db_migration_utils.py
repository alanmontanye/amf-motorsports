"""
Database migration utilities to help move data from SQLite to PostgreSQL when deploying
"""
import os
import json
import tempfile
from app import create_app, db
from app.utils.data_management import export_data, import_data
from flask import current_app

def migrate_to_postgres():
    """
    Migrate data from SQLite to PostgreSQL
    Steps:
    1. Export all data from SQLite to a JSON file
    2. Switch database connection to PostgreSQL
    3. Import data into PostgreSQL
    """
    # Create a temp file for the data
    temp_file = tempfile.mktemp(suffix='.json')
    
    # Export data using SQLite connection
    print("Exporting data from SQLite...")
    # Create app with default SQLite connection
    sqlite_app = create_app('development')
    with sqlite_app.app_context():
        export_data(temp_file)
    
    print(f"Data exported to {temp_file}")
    
    # Now switch to PostgreSQL and import
    print("Importing data to PostgreSQL...")
    pg_app = create_app('production')
    with pg_app.app_context():
        # Create tables
        db.create_all()
        
        # Import data
        import_data(temp_file, clear_existing=True)
    
    print("Migration completed successfully")
    
    # Clean up the temp file
    os.unlink(temp_file)

def backup_production_db():
    """
    Create a backup of the production database
    """
    # Create app with production configuration
    app = create_app('production')
    with app.app_context():
        # Generate a timestamped filename
        backup_path = export_data()
        print(f"Production database backed up to: {backup_path}")
        return backup_path

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python db_migration_utils.py [migrate|backup]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'migrate':
        migrate_to_postgres()
    elif action == 'backup':
        backup_production_db()
    else:
        print(f"Unknown action: {action}")
        print("Usage: python db_migration_utils.py [migrate|backup]")
        sys.exit(1)
