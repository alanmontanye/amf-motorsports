"""
Database initialization script to create all tables and add sample data if needed
"""
from app import create_app, db
from app.models import ATV, Expense, Sale, Part, Image, EbayListing, Storage

def init_db(with_sample_data=False):
    """Initialize the database with all required tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("All database tables created successfully!")
        
        # Check if Storage table has any entries
        if with_sample_data and Storage.query.count() == 0:
            # Add basic storage locations
            storage_locations = [
                Storage(name="Main Garage", description="Primary workspace and storage"),
                Storage(name="Shed", description="Outdoor storage for larger parts"),
                Storage(name="Parts Cabinet", description="Organized shelving for small parts"),
                Storage(name="Offsite Storage", description="Rental unit for overflow")
            ]
            
            for storage in storage_locations:
                db.session.add(storage)
            
            db.session.commit()
            print(f"Added {len(storage_locations)} sample storage locations")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize the AMF Motorsports database")
    parser.add_argument('--sample', action='store_true', help='Add sample data to the database')
    
    args = parser.parse_args()
    init_db(with_sample_data=args.sample)
