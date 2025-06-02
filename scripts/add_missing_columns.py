#!/usr/bin/env python3
"""
Add missing database columns for parting workflow
This script safely adds the missing columns that are causing deployment failures
"""

import sys
import os
import sqlite3
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ATV, Part

def add_missing_columns():
    """Add missing columns to the database"""
    
    # Create app and get database path
    app = create_app()
    
    with app.app_context():
        # Get the database path from the SQLAlchemy URI
        database_uri = app.config.get('DATABASE_URL') or app.config.get('SQLALCHEMY_DATABASE_URI')
        
        if database_uri.startswith('sqlite:///'):
            db_path = database_uri.replace('sqlite:///', '')
        else:
            print("This script only works with SQLite databases")
            return False
            
        # Connect to the database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if parting_status column exists in atv table
            cursor.execute("PRAGMA table_info(atv)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns to ATV table if they don't exist
            if 'parting_status' not in columns:
                print("Adding parting_status column to atv table...")
                cursor.execute("ALTER TABLE atv ADD COLUMN parting_status VARCHAR(20) DEFAULT 'intact'")
                
            if 'machine_id' not in columns:
                print("Adding machine_id column to atv table...")
                cursor.execute("ALTER TABLE atv ADD COLUMN machine_id VARCHAR(50)")
                
            # Check if condition column exists in part table
            cursor.execute("PRAGMA table_info(part)")
            part_columns = [column[1] for column in cursor.fetchall()]
            
            if 'condition' not in part_columns:
                print("Adding condition column to part table...")
                cursor.execute("ALTER TABLE part ADD COLUMN condition VARCHAR(20) DEFAULT 'good'")
                
            # Commit the changes
            conn.commit()
            print("Successfully added missing columns!")
            return True
            
        except Exception as e:
            print(f"Error adding columns: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()

def verify_columns():
    """Verify that all required columns exist"""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to query ATV with the new columns
            atv_count = ATV.query.count()
            print(f"✓ ATV table accessible with {atv_count} records")
            
            # Try to query Part with condition column
            part_count = Part.query.count()
            print(f"✓ Part table accessible with {part_count} records")
            
            return True
        except Exception as e:
            print(f"✗ Database verification failed: {e}")
            return False

if __name__ == '__main__':
    print("Adding missing database columns...")
    
    if add_missing_columns():
        print("\nVerifying database structure...")
        if verify_columns():
            print("\n✓ Database migration completed successfully!")
            print("You can now run the application without column errors.")
        else:
            print("\n✗ Database verification failed.")
    else:
        print("\n✗ Failed to add missing columns.")
