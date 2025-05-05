"""
Fix database script that adds hours tracking columns to ATV table and sets default values
"""
import os
import sqlite3
from datetime import datetime

def fix_database():
    """Add hours columns to ATV table and set default values"""
    try:
        # Get the app.db path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
        print(f"Database path: {db_path}")
        
        # Create backup of the database
        backup_path = f"app.db.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Created backup at {backup_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(atv)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        # Add columns that don't exist
        for column_name in ['acquisition_hours', 'repair_hours', 'selling_hours', 'total_hours']:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE atv ADD COLUMN {column_name} FLOAT DEFAULT 0")
                    print(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e):
                        print(f"Column {column_name} already exists")
                    else:
                        print(f"Error adding {column_name}: {e}")
        
        # Update all rows to make sure they have default values
        cursor.execute("UPDATE atv SET acquisition_hours = 0 WHERE acquisition_hours IS NULL")
        cursor.execute("UPDATE atv SET repair_hours = 0 WHERE repair_hours IS NULL")
        cursor.execute("UPDATE atv SET selling_hours = 0 WHERE selling_hours IS NULL")
        cursor.execute("UPDATE atv SET total_hours = 0 WHERE total_hours IS NULL")
        print("Updated existing records with default values")
        
        # Calculate total hours
        cursor.execute("UPDATE atv SET total_hours = COALESCE(acquisition_hours, 0) + COALESCE(repair_hours, 0) + COALESCE(selling_hours, 0)")
        print("Updated total_hours field based on component hours")
        
        # Commit and close
        conn.commit()
        print("Changes committed to database")
        conn.close()
        
        print("Database fix completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

if __name__ == "__main__":
    fix_database()
