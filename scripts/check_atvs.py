"""
Script to check existing ATVs in the database
"""
import os
import sys
from sqlalchemy import text

# Make sure we can import from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db, create_app
from app.models import ATV

print("Checking ATVs in database...")

# Create app with production config to use the right DATABASE_URL
app = create_app('production')

with app.app_context():
    # Count ATVs by status
    statuses = db.session.execute(text("SELECT status, COUNT(*) FROM atv GROUP BY status")).fetchall()
    print("\nATV counts by status:")
    for status, count in statuses:
        print(f"  {status}: {count}")
    
    # Get total count
    total_count = db.session.execute(text("SELECT COUNT(*) FROM atv")).scalar()
    print(f"\nTotal ATVs in database: {total_count}")
    
    # Sample data from first 5 ATVs to verify structure
    if total_count > 0:
        print("\nSample ATVs (first 5):")
        atvs = ATV.query.limit(5).all()
        for atv in atvs:
            print(f"  ID: {atv.id}, Make: {atv.make}, Model: {atv.model}, Year: {atv.year}, Status: {atv.status}")
    
    # If no ATVs are found, check if there might be data in a different format
    if total_count == 0:
        print("\nNo ATVs found. Checking for any table data...")
        column_names = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'atv'")).fetchall()
        print(f"Available columns: {', '.join(col[0] for col in column_names)}")
        
        # Try a simple select to see any data
        try:
            raw_data = db.session.execute(text("SELECT * FROM atv LIMIT 5")).fetchall()
            if raw_data:
                print(f"\nFound {len(raw_data)} raw ATV records. First record:")
                for i, value in enumerate(raw_data[0]):
                    print(f"  {column_names[i][0]}: {value}")
        except Exception as e:
            print(f"Error trying to read raw data: {str(e)}")
