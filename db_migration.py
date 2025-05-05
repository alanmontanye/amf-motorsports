"""
Migration script to add hours tracking fields to the ATV database table.
"""
import os
import sqlite3

def add_columns_to_atv_table():
    """Add hours tracking columns to the ATV table if they don't already exist."""
    # Get the database file path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add columns with exception handling
    columns_to_add = [
        "acquisition_hours FLOAT DEFAULT 0",
        "repair_hours FLOAT DEFAULT 0",
        "selling_hours FLOAT DEFAULT 0",
        "total_hours FLOAT DEFAULT 0"
    ]
    
    for column_def in columns_to_add:
        column_name = column_def.split()[0]
        try:
            alter_query = f"ALTER TABLE atv ADD COLUMN {column_def}"
            print(f"Executing: {alter_query}")
            cursor.execute(alter_query)
            print(f"Added column {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print(f"Column {column_name} already exists, skipping.")
            else:
                print(f"Error adding column {column_name}: {e}")
    
    # Update existing records to ensure they have values
    cursor.execute("UPDATE atv SET acquisition_hours = 0 WHERE acquisition_hours IS NULL")
    cursor.execute("UPDATE atv SET repair_hours = 0 WHERE repair_hours IS NULL")
    cursor.execute("UPDATE atv SET selling_hours = 0 WHERE selling_hours IS NULL")
    cursor.execute("UPDATE atv SET total_hours = 0 WHERE total_hours IS NULL")
    print("Updated existing records with default values")
    
    # Commit and close
    conn.commit()
    conn.close()
    print("Migration completed")

if __name__ == "__main__":
    add_columns_to_atv_table()
