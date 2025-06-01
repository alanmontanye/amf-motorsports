#!/usr/bin/env python
"""
Initialize parting data for existing ATVs

This script ensures all existing ATVs have valid parting_status and machine_id values.
Run this script after applying the database migration to ensure data consistency.
"""

import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import ATV, Part

app = create_app()

def initialize_parting_data():
    """Initialize parting_status and machine_id for all ATVs that don't have them"""
    with app.app_context():
        # Get all ATVs
        atvs = ATV.query.all()
        
        updated_count = 0
        total_count = len(atvs)
        
        print(f"Checking {total_count} ATVs for parting data initialization...")
        
        for atv in atvs:
            updated = False
            
            # Check if parting_status is None or empty
            if atv.parting_status is None or atv.parting_status == '':
                # Default to 'whole' but check if it has parts first
                parts_count = Part.query.filter_by(atv_id=atv.id).count()
                
                if parts_count > 0:
                    atv.parting_status = 'parting_out'
                else:
                    atv.parting_status = 'whole'
                
                updated = True
                print(f"Set parting_status to '{atv.parting_status}' for ATV {atv.id}: {atv.year} {atv.make} {atv.model}")
            
            # Check if machine_id is None or empty
            if atv.machine_id is None or atv.machine_id == '':
                atv.machine_id = str(uuid.uuid4())
                updated = True
                print(f"Set machine_id to '{atv.machine_id}' for ATV {atv.id}: {atv.year} {atv.make} {atv.model}")
            
            if updated:
                updated_count += 1
        
        # Commit changes if any
        if updated_count > 0:
            db.session.commit()
            print(f"Updated {updated_count} ATVs")
        else:
            print("No ATVs needed updating")

if __name__ == '__main__':
    initialize_parting_data()
    print("Parting data initialization complete")
