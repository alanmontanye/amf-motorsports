"""
Recreate database tables to ensure they match the models
"""
import os
from app import create_app, db
from app.models import ATV, Part, Image, Storage, Expense, Sale

def recreate_tables():
    """Drop and recreate all database tables"""
    try:
        app = create_app()
        with app.app_context():
            # Check if we need to back up the database first
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
            if os.path.exists(db_path):
                print(f"Database exists at {db_path}")
                backup_path = f"app.db.backup-{app.config.get('ENV', 'dev')}"
                print(f"Creating backup at {backup_path}")
                with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            
            # Drop all tables
            print("Dropping all tables...")
            db.drop_all()
            print("All tables dropped")
            
            # Create tables
            print("Creating tables...")
            db.create_all()
            print("Tables created successfully")
            
            # Verify table structure
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            # Check ATV table specifically
            if 'atv' in tables:
                columns = inspector.get_columns('atv')
                print("\nATV table columns:")
                for column in columns:
                    print(f"  {column['name']} ({column['type']})")
                
                # Verify hours columns
                hour_columns = ['acquisition_hours', 'repair_hours', 'selling_hours', 'total_hours']
                for col in hour_columns:
                    found = any(column['name'] == col for column in columns)
                    print(f"  Column {col} exists: {found}")
            
            return True
            
    except Exception as e:
        print(f"Error recreating tables: {e}")
        return False

if __name__ == "__main__":
    recreate_tables()
