"""
Script to check and fix database schema issues
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Make sure we can import from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db, create_app
from app.models import ATV, Part  # Import models to ensure all columns are defined

print("Starting database schema fix script...")

# Create app with production config to use the right DATABASE_URL
app = create_app('production')

with app.app_context():
    try:
        # Get database connection
        engine = db.engine
        inspector = inspect(engine)
        
        print("Connected to database successfully")
        
        # Check if atv table exists
        if 'atv' not in inspector.get_table_names():
            print("ERROR: 'atv' table does not exist! Creating all tables...")
            db.create_all()
            print("Tables created. Please restart your application.")
        else:
            print("'atv' table exists, checking columns...")
            
            # Get columns in the atv table
            columns = [column['name'] for column in inspector.get_columns('atv')]
            print(f"Found columns: {', '.join(columns)}")
            
            # Check for missing columns
            required_columns = {
                'status': "VARCHAR(20) DEFAULT 'active'",
                'parting_status': "VARCHAR(20) DEFAULT 'whole'",
                'machine_id': "VARCHAR(64)"
            }
            
            missing_columns = []
            for column, definition in required_columns.items():
                if column not in columns:
                    missing_columns.append((column, definition))
            
            if not missing_columns:
                print("No missing columns found in the atv table!")
            else:
                print(f"Found {len(missing_columns)} missing columns in the atv table:")
                
                # Add missing columns
                for column, definition in missing_columns:
                    print(f"Adding missing column '{column}' with definition '{definition}'")
                    try:
                        query = text(f"ALTER TABLE atv ADD COLUMN {column} {definition};")
                        db.session.execute(query)
                        print(f"  -> Added '{column}' successfully")
                    except SQLAlchemyError as e:
                        print(f"  -> Error adding '{column}': {str(e)}")
                
                # Commit changes
                db.session.commit()
                print("All missing columns added successfully.")
            
            # Also check the Part table for the condition column
            if 'part' in inspector.get_table_names():
                part_columns = [column['name'] for column in inspector.get_columns('part')]
                if 'condition' not in part_columns:
                    print("'condition' column missing from Part table, adding it...")
                    try:
                        query = text("ALTER TABLE part ADD COLUMN condition VARCHAR(20);")
                        db.session.execute(query)
                        db.session.commit()
                        print("  -> Added 'condition' column to Part table successfully")
                    except SQLAlchemyError as e:
                        print(f"  -> Error adding 'condition' to Part table: {str(e)}")
            
        # Test query to make sure it works
        try:
            active_count = ATV.query.filter_by(status='active').count()
            print(f"Test query successful: Found {active_count} active ATVs")
        except SQLAlchemyError as e:
            print(f"Test query failed: {str(e)}")

        print("Schema check and fix complete!")
        
    except SQLAlchemyError as e:
        print(f"Database connection error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
