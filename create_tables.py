"""
Create database tables from models
"""
from app import create_app, db
from app.models import ATV, Part, Image, Storage, Expense, Sale

def create_tables():
    """Create all database tables"""
    try:
        app = create_app()
        with app.app_context():
            # Create tables
            db.create_all()
            print("Successfully created all database tables")
            
            # Check what tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            # For each table, print columns
            for table in tables:
                columns = inspector.get_columns(table)
                print(f"\nTable '{table}' columns:")
                for column in columns:
                    print(f"  {column['name']} ({column['type']})")
            
            return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()
