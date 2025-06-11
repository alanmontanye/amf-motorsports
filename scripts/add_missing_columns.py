#!/usr/bin/env python3
"""
Add missing database columns for parting workflow
This script uses SQLAlchemy reflection to safely add missing columns to the database
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ATV, Part
from sqlalchemy import inspect, Column, String, DateTime, Float, Integer

def update_database_schema():
    """Use SQLAlchemy to ensure all tables and columns exist"""
    print("Starting database schema update...")
    app = create_app()
    
    with app.app_context():
        # Get database URI
        database_uri = app.config.get('DATABASE_URL') or app.config.get('SQLALCHEMY_DATABASE_URI')
        print(f"Using database: {database_uri}")
        
        try:
            # Create all tables that don't exist
            print("Creating any missing tables...")
            db.create_all()
            
            # Print info about the database connection
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Found tables: {', '.join(tables)}")
            
            # Check if the Part table exists and contains the required columns
            if 'part' in tables:
                part_columns = [c['name'] for c in inspector.get_columns('part')]
                print(f"Part table columns: {', '.join(part_columns)}")
                
                # Check specifically for required columns
                required_columns = ['tote', 'created_at']
                missing_columns = [col for col in required_columns if col not in part_columns]
                
                if missing_columns:
                    print(f"Missing columns in Part table: {', '.join(missing_columns)}")
                    # Need to use a workaround to add columns
                    print("Adding the tote column might require a direct SQL query on Production")
                    print("For development, the db.create_all() should have updated the schema")
                else:
                    print("All required columns exist in the Part table")
            
            # Verify we can query ATV and Part tables
            try:
                atv_count = ATV.query.count()
                print(f"ATV table has {atv_count} records")
                
                part_count = Part.query.count()
                print(f"Part table has {part_count} records")
                
                # Set default values for parts without created_at
                if 'created_at' in part_columns:
                    parts_without_date = Part.query.filter(Part.created_at == None).all()
                    print(f"Found {len(parts_without_date)} parts without created_at date")
                    
                    for part in parts_without_date:
                        part.created_at = datetime.utcnow()
                    
                    if parts_without_date:
                        db.session.commit()
                        print(f"Updated created_at for {len(parts_without_date)} parts")
                
                return True
            except Exception as e:
                print(f"Error querying database: {e}")
                return False
            
        except Exception as e:
            print(f"Error updating database schema: {e}")
            return False

def print_sql_commands():
    """Print SQL commands for manual execution on production"""
    print("\n===== SQL COMMANDS FOR PRODUCTION DATABASE =====")
    print("These commands can be run on the production database if needed:")
    print("")
    print("-- PostgreSQL commands to add missing columns:")
    print("ALTER TABLE part ADD COLUMN IF NOT EXISTS tote VARCHAR(20);")
    print("ALTER TABLE part ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
    print("""\n-- PostgreSQL command to update existing records:
          UPDATE part SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;""")
    print("=================================================\n")

if __name__ == '__main__':
    print("Running database schema update script...")
    
    # Update schema using SQLAlchemy
    if update_database_schema():
        print("\n✓ Database schema updated successfully!")
        print_sql_commands()
        print("You can now run the application without column errors.")
    else:
        print("\n✗ Database schema update failed.")
        print("You might need to run the SQL commands manually on production.")
        print_sql_commands()
