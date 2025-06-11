"""
Direct PostgreSQL script to add missing columns to the Render database
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Render PostgreSQL connection details
DB_HOST = "dpg-d0cjkjh5pdvs73a4bl70-a"  # Render database hostname
DB_NAME = "amf_db_q8kx"                 # Database name
DB_USER = "amf_db_q8kx_user"            # Database user
DB_PASS = "JHLHRvCg4Qb0ofFKfCkbVOWG5qgIFEFh"  # Database password
DB_PORT = "5432"                        # PostgreSQL default port

def main():
    print("Connecting to Render PostgreSQL database directly...")
    
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print(f"Successfully connected to {DB_NAME} on {DB_HOST}")
        
        # Check if the atv table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'atv')")
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("ERROR: 'atv' table does not exist! Database might be empty or incorrectly named.")
            return
        
        # Get current columns in the atv table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'atv'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Found columns: {', '.join(columns)}")
        
        # Add missing columns
        required_columns = {
            'parting_status': "VARCHAR(20) DEFAULT 'whole'",
            'machine_id': "VARCHAR(64)"
        }
        
        for column, definition in required_columns.items():
            if column not in columns:
                print(f"Adding missing column '{column}' with definition '{definition}'")
                try:
                    cursor.execute(
                        sql.SQL("ALTER TABLE atv ADD COLUMN {} {}").format(
                            sql.Identifier(column), 
                            sql.SQL(definition)
                        )
                    )
                    print(f"  -> Added '{column}' successfully")
                except Exception as e:
                    print(f"  -> Error adding '{column}': {str(e)}")
            else:
                print(f"Column '{column}' already exists")
        
        # Update any null status values to 'active'
        cursor.execute("UPDATE atv SET status = 'active' WHERE status IS NULL")
        updated_rows = cursor.rowcount
        print(f"Updated {updated_rows} rows with NULL status to 'active'")
        
        # Check part table for condition column
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'part')")
        part_table_exists = cursor.fetchone()[0]
        
        if part_table_exists:
            cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'part' AND column_name = 'condition')")
            condition_exists = cursor.fetchone()[0]
            
            if not condition_exists:
                print("Adding 'condition' column to part table...")
                cursor.execute("ALTER TABLE part ADD COLUMN condition VARCHAR(20)")
                print("  -> Added 'condition' column successfully")
        
        # Get ATV counts by status
        print("\nCurrent ATV counts by status:")
        cursor.execute("SELECT status, COUNT(*) FROM atv GROUP BY status")
        status_counts = cursor.fetchall()
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
        # Get total ATV count
        cursor.execute("SELECT COUNT(*) FROM atv")
        total_count = cursor.fetchone()[0]
        print(f"\nTotal ATVs in database: {total_count}")
        
        print("\nSchema fix complete! Your application should now work correctly.")
        print("Please restart your Render web service to ensure changes take effect.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

if __name__ == "__main__":
    main()
