"""
Migrate the database to add hours tracking columns using SQLAlchemy
"""
from app import db, create_app
from sqlalchemy import Column, Float
import sqlalchemy as sa
from alembic import op
import os

app = create_app()

with app.app_context():
    print("Connected to database")
    
    # Get database engine
    engine = db.engine
    conn = engine.connect()
    
    # Check if table has the columns
    inspector = sa.inspect(engine)
    columns = inspector.get_columns('atv')
    column_names = [col['name'] for col in columns]
    print(f"Existing columns: {column_names}")
    
    # Add columns if they don't exist
    with conn.begin():
        # Create a metadata object
        metadata = sa.MetaData()
        
        # Reflect the existing table
        atv_table = sa.Table('atv', metadata, autoload_with=engine)
        
        # Define the new columns
        new_columns = [
            ('acquisition_hours', Float),
            ('repair_hours', Float),
            ('selling_hours', Float),
            ('total_hours', Float)
        ]
        
        # Add each column if it doesn't exist
        for col_name, col_type in new_columns:
            if col_name not in column_names:
                try:
                    print(f"Adding column {col_name}")
                    column = sa.Column(col_name, col_type, server_default='0')
                    conn.execute(sa.text(f"ALTER TABLE atv ADD COLUMN {col_name} FLOAT DEFAULT 0"))
                    print(f"Successfully added column {col_name}")
                except sa.exc.OperationalError as e:
                    print(f"Error adding column {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists")
    
    # Set default values for existing records
    with conn.begin():
        try:
            print("Setting default values for NULL fields")
            conn.execute(sa.text("UPDATE atv SET acquisition_hours = 0 WHERE acquisition_hours IS NULL"))
            conn.execute(sa.text("UPDATE atv SET repair_hours = 0 WHERE repair_hours IS NULL"))
            conn.execute(sa.text("UPDATE atv SET selling_hours = 0 WHERE selling_hours IS NULL"))
            conn.execute(sa.text("UPDATE atv SET total_hours = 0 WHERE total_hours IS NULL"))
            
            # Compute total hours
            conn.execute(sa.text("UPDATE atv SET total_hours = COALESCE(acquisition_hours, 0) + COALESCE(repair_hours, 0) + COALESCE(selling_hours, 0)"))
            print("Successfully updated records with default values")
        except sa.exc.OperationalError as e:
            print(f"Error updating records: {e}")
    
    # Verify the new columns
    inspector = sa.inspect(engine)
    updated_columns = inspector.get_columns('atv')
    updated_column_names = [col['name'] for col in updated_columns]
    print(f"\nVerified columns after update: {updated_column_names}")
    
    conn.close()
    print("Database migration completed!")
