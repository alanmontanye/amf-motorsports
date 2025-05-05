"""
Database migration to add hours tracking columns to ATV table
"""
import sqlite3
import os
import sys

def migrate_database():
    """Add hours tracking columns to ATV table and set default values"""
    try:
        # Get the database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
        print(f"Database path: {db_path}")
        
        # Create backup of the database
        backup_path = f"app.db.backup-hours-migration"
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Created backup at {backup_path}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing schema
        cursor.execute("PRAGMA table_info(atv)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current ATV table columns: {columns}")
        
        # Add the hours columns if they don't exist
        for column in ['acquisition_hours', 'repair_hours', 'selling_hours', 'total_hours']:
            if column not in columns:
                print(f"Adding column {column}...")
                cursor.execute(f"ALTER TABLE atv ADD COLUMN {column} FLOAT DEFAULT 0")
            else:
                print(f"Column {column} already exists")
        
        # Update existing records to ensure they have values
        print("Setting default values for existing records...")
        cursor.execute("UPDATE atv SET acquisition_hours = 0 WHERE acquisition_hours IS NULL")
        cursor.execute("UPDATE atv SET repair_hours = 0 WHERE repair_hours IS NULL")
        cursor.execute("UPDATE atv SET selling_hours = 0 WHERE selling_hours IS NULL")
        cursor.execute("UPDATE atv SET total_hours = 0 WHERE total_hours IS NULL")
        
        # Calculate total hours for existing records
        print("Calculating total hours...")
        cursor.execute("""
            UPDATE atv 
            SET total_hours = COALESCE(acquisition_hours, 0) + COALESCE(repair_hours, 0) + COALESCE(selling_hours, 0)
            WHERE total_hours = 0 OR total_hours IS NULL
        """)
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(atv)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Updated ATV table columns: {columns}")
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    print("Starting hours tracking migration...")
    if migrate_database():
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
