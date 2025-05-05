from app import create_app, db

app = create_app()
with app.app_context():
    db.drop_all()  # Drop existing tables
    db.create_all()  # Create all tables
    print("Database tables created successfully!")
