"""
Migration script to add updated_at field to Part model
"""
import os
import sys
from sqlalchemy import create_engine, text, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import sqlite
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from flask import Flask
from app import db, create_app

def run_migration():
    """Run the migration to add updated_at field to Part model"""
    app = create_app()
    
    with app.app_context():
        # Check if updated_at column exists in Part table
        inspector = db.inspect(db.engine)
        part_columns = [column['name'] for column in inspector.get_columns('part')]
        
        # Add updated_at column to Part table if it doesn't exist
        if 'updated_at' not in part_columns:
            print("Adding 'updated_at' column to Part table...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE part ADD COLUMN updated_at DATETIME'))
                # Set default value for existing records to current time
                current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                conn.execute(text(f"UPDATE part SET updated_at = '{current_time}' WHERE updated_at IS NULL"))
                conn.commit()
            print("Successfully added 'updated_at' column to Part table.")
        else:
            print("'updated_at' column already exists in Part table.")
            
        print("Migration completed successfully!")

if __name__ == '__main__':
    run_migration()
