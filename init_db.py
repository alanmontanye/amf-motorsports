from app import create_app, db
from app.models import ATV, Part, Expense, Sale, Image, EbayListing, Storage
from config import Config

def init_db():
    app = create_app(Config)
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all existing tables.")
        
        # Create all tables
        db.create_all()
        print("Created all database tables.")
        
        # Add initial storage locations
        storage_locations = [
            'Garage Shelf A',
            'Garage Shelf B',
            'Garage Shelf C',
            'Storage Room 1',
            'Storage Room 2',
            'Attic'
        ]
        
        for name in storage_locations:
            storage = Storage(name=name)
            db.session.add(storage)
        
        db.session.commit()
        print("Added initial storage locations.")

if __name__ == '__main__':
    init_db()
