"""Run the hours migration script"""
from app import create_app, db
from sqlalchemy import Column, Float

def run_migration():
    """Run migration to add hours columns"""
    app = create_app()
    with app.app_context():
        # Add hour fields to ATV table
        try:
            # Use ALTER TABLE directly with SQLAlchemy
            db.engine.execute('ALTER TABLE atv ADD COLUMN acquisition_hours FLOAT')
            db.engine.execute('ALTER TABLE atv ADD COLUMN repair_hours FLOAT')
            db.engine.execute('ALTER TABLE atv ADD COLUMN selling_hours FLOAT') 
            db.engine.execute('ALTER TABLE atv ADD COLUMN total_hours FLOAT')
            print("Successfully added hours columns to ATV table!")
        except Exception as e:
            # If columns already exist, just show a message
            print(f"Note: Some columns may already exist: {e}")

if __name__ == '__main__':
    run_migration()
