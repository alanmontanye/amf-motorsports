"""
Check database tables
"""
import sqlite3
import os

def check_database():
    """Check what tables exist in the database"""
    try:
        # Get the database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
        print(f"Database path: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"ERROR: Database file not found at {db_path}")
            return False
            
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # For each table, print the schema
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"\nTable '{table[0]}' schema:")
            for col in columns:
                print(f"  {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database()
