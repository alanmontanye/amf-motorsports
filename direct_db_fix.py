"""
Direct database fix for adding hours tracking columns
"""
import sqlite3
import os

# Find the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
print(f"Looking for database at: {db_path}")

if not os.path.exists(db_path):
    print(f"ERROR: Database file not found at {db_path}")
    exit(1)

print(f"Database found at {db_path}, connecting...")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check the current schema
    print("Current schema for ATV table:")
    cursor.execute("PRAGMA table_info(atv)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col}")
    
    # Add the columns directly
    print("\nAdding new columns...")
    
    try:
        cursor.execute("ALTER TABLE atv ADD COLUMN acquisition_hours FLOAT DEFAULT 0")
        print("Added acquisition_hours")
    except sqlite3.OperationalError as e:
        print(f"Error adding acquisition_hours: {e}")
    
    try:
        cursor.execute("ALTER TABLE atv ADD COLUMN repair_hours FLOAT DEFAULT 0")
        print("Added repair_hours")
    except sqlite3.OperationalError as e:
        print(f"Error adding repair_hours: {e}")
    
    try:
        cursor.execute("ALTER TABLE atv ADD COLUMN selling_hours FLOAT DEFAULT 0")
        print("Added selling_hours")
    except sqlite3.OperationalError as e:
        print(f"Error adding selling_hours: {e}")
    
    try:
        cursor.execute("ALTER TABLE atv ADD COLUMN total_hours FLOAT DEFAULT 0")
        print("Added total_hours")
    except sqlite3.OperationalError as e:
        print(f"Error adding total_hours: {e}")
    
    # Update existing records
    print("\nUpdating existing records...")
    cursor.execute("UPDATE atv SET acquisition_hours = 0 WHERE acquisition_hours IS NULL")
    cursor.execute("UPDATE atv SET repair_hours = 0 WHERE repair_hours IS NULL")
    cursor.execute("UPDATE atv SET selling_hours = 0 WHERE selling_hours IS NULL")
    cursor.execute("UPDATE atv SET total_hours = 0 WHERE total_hours IS NULL")
    
    # Compute total hours
    cursor.execute("UPDATE atv SET total_hours = acquisition_hours + repair_hours + selling_hours")
    
    # Commit the changes
    conn.commit()
    print("Changes committed to database")
    
    # Verify the new schema
    print("\nVerifying new schema:")
    cursor.execute("PRAGMA table_info(atv)")
    new_columns = cursor.fetchall()
    for col in new_columns:
        print(f"  {col}")
    
    # Close the connection
    conn.close()
    print("\nDatabase update completed successfully!")
    
except Exception as e:
    print(f"ERROR: {e}")
