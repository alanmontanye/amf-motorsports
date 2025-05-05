"""
Migration script to add VIN field to ATV model and update image type field
"""
import os
import sys
from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import sqlite

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from flask import Flask
from app import db, create_app

def run_migration():
    """Run the migration to add VIN field to ATV and image_type to Image"""
    app = create_app()
    
    with app.app_context():
        # Check if VIN column exists in ATV table
        inspector = db.inspect(db.engine)
        atv_columns = [column['name'] for column in inspector.get_columns('atv')]
        image_columns = [column['name'] for column in inspector.get_columns('image')]
        
        # Add VIN column to ATV table if it doesn't exist
        if 'vin' not in atv_columns:
            print("Adding 'vin' column to ATV table...")
            db.engine.execute('ALTER TABLE atv ADD COLUMN vin VARCHAR(128)')
            print("Successfully added 'vin' column to ATV table.")
        else:
            print("'vin' column already exists in ATV table.")
        
        # Add image_type column to Image table if it doesn't exist
        if 'image_type' not in image_columns:
            print("Adding 'image_type' column to Image table...")
            db.engine.execute('ALTER TABLE image ADD COLUMN image_type VARCHAR(64)')
            # Set default value for existing records
            db.engine.execute("UPDATE image SET image_type = 'general' WHERE image_type IS NULL")
            print("Successfully added 'image_type' column to Image table.")
        else:
            print("'image_type' column already exists in Image table.")
            
        print("Migration completed successfully!")

if __name__ == '__main__':
    run_migration()
