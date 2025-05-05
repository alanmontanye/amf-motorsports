"""
Fix database by adding hours tracking columns
"""
from app import create_app, db
from app.models import ATV
import sqlite3
import os

def add_columns_to_db():
    """Add hours tracking columns to the database"""
    app = create_app()
    
    with app.app_context():
        print("Connected to database")
        
        # Get the database file path
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri[10:]  # Remove 'sqlite:///' prefix
            print(f"Database path: {db_path}")
            
            # Get absolute path
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
                print(f"Absolute database path: {db_path}")
            
            # Connect directly to SQLite
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if columns exist
                cursor.execute("PRAGMA table_info(atv)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"Existing columns: {columns}")
                
                # Add missing columns
                for column in ['acquisition_hours', 'repair_hours', 'selling_hours', 'total_hours']:
                    if column not in columns:
                        try:
                            query = f"ALTER TABLE atv ADD COLUMN {column} FLOAT DEFAULT 0"
                            print(f"Executing: {query}")
                            cursor.execute(query)
                            print(f"Added column {column}")
                        except sqlite3.OperationalError as e:
                            print(f"Error adding column {column}: {e}")
                
                # Update values
                cursor.execute("UPDATE atv SET acquisition_hours = 0 WHERE acquisition_hours IS NULL")
                cursor.execute("UPDATE atv SET repair_hours = 0 WHERE repair_hours IS NULL")
                cursor.execute("UPDATE atv SET selling_hours = 0 WHERE selling_hours IS NULL")
                cursor.execute("UPDATE atv SET total_hours = 0 WHERE total_hours IS NULL")
                
                conn.commit()
                print("Database updated successfully!")
                conn.close()
                
            except Exception as e:
                print(f"Error working with database: {e}")
        else:
            print(f"Non-SQLite database URI: {db_uri}")
            print("This script only supports SQLite databases")

if __name__ == "__main__":
    add_columns_to_db()
