"""
Add test data to database
"""
from app import create_app, db
from app.models import ATV
from datetime import datetime, date, timedelta

def add_test_data():
    """Add test ATV with hour tracking data"""
    try:
        app = create_app()
        with app.app_context():
            # Add a test ATV with hour tracking
            test_atv = ATV(
                make="Honda",
                model="TRX450R",
                year=2020,
                vin="TEST12345678901",
                status="active",
                purchase_date=date.today() - timedelta(days=30),
                purchase_price=2500.00,
                purchase_location="Test Dealership",
                description="Test ATV with hour tracking data",
                acquisition_hours=5.5,
                repair_hours=10.0,
                selling_hours=2.5,
                total_hours=18.0  # Should be calculated by method but set manually for test
            )
            
            # Check if ATV with same VIN already exists
            existing = ATV.query.filter_by(vin="TEST12345678901").first()
            if existing:
                print("Test ATV already exists, updating instead of adding")
                existing.acquisition_hours = 5.5
                existing.repair_hours = 10.0
                existing.selling_hours = 2.5
                existing.update_total_hours()
                db.session.commit()
            else:
                db.session.add(test_atv)
                db.session.commit()
                print(f"Added test ATV: {test_atv.year} {test_atv.make} {test_atv.model}")
            
            # Verify the ATV was added with hour tracking
            added_atv = ATV.query.filter_by(vin="TEST12345678901").first()
            if added_atv:
                print(f"\nTest ATV data:")
                print(f"  Make/Model: {added_atv.year} {added_atv.make} {added_atv.model}")
                print(f"  Acquisition Hours: {added_atv.acquisition_hours}")
                print(f"  Repair Hours: {added_atv.repair_hours}")
                print(f"  Selling Hours: {added_atv.selling_hours}")
                print(f"  Total Hours: {added_atv.total_hours}")
                print(f"  Hourly Profit Rate: ${added_atv.hourly_profit_rate():.2f}/hr")
                return True
            else:
                print("Failed to add test ATV")
                return False
            
    except Exception as e:
        print(f"Error adding test data: {e}")
        return False

if __name__ == "__main__":
    add_test_data()
