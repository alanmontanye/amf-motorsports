"""
Script to check and fix database schema issues on Render
This can be run directly on Render via the Web Service Console

Environment variables required:
- DATABASE_URL: The PostgreSQL connection URL
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Make sure the script works stand-alone on Render
try:
    # Add parent directory to path so we can import app
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app import db, create_app
    print("Successfully imported app modules")
except Exception as e:
    print(f"Error importing app modules: {e}")
    sys.exit(1)

def main():
    print("Starting database schema fix script for Render PostgreSQL...")
    
    # Create app with production config to use the DATABASE_URL
    app = create_app('production')
    
    with app.app_context():
        try:
            # Get database connection
            engine = db.engine
            inspector = inspect(engine)
            
            print(f"Successfully connected to database: {engine.url}")
            
            # Check if atv table exists
            if 'atv' not in inspector.get_table_names():
                print("ERROR: 'atv' table does not exist! Creating all tables...")
                db.create_all()
                print("Tables created. Please restart your application.")
                return
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
                
            # Count ATVs by status
            statuses = db.session.execute(text("SELECT status, COUNT(*) FROM atv GROUP BY status")).fetchall()
            print("\nATV counts by status:")
            for status, count in statuses:
                print(f"  {status}: {count}")
            
            # Get total count
            total_count = db.session.execute(text("SELECT COUNT(*) FROM atv")).scalar()
            print(f"\nTotal ATVs in database: {total_count}")
                
            # Update ATVs that might have NULL status
            if total_count > 0:
                try:
                    update_query = text("UPDATE atv SET status = 'active' WHERE status IS NULL")
                    result = db.session.execute(update_query)
                    db.session.commit()
                    print(f"\nUpdated {result.rowcount} ATVs with NULL status to 'active'")
                except SQLAlchemyError as e:
                    print(f"Error updating NULL statuses: {str(e)}")
            
            print("\nSchema check and fix complete!")
            
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
