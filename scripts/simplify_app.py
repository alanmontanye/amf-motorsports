"""
Script to simplify the ATV inventory app by:
1. Removing references to eBay functionality
2. Simplifying the database schema
3. Making the app more resilient to errors
"""
import os
import sys
import shutil
from pathlib import Path

# Add the parent directory to sys.path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import ATV, Part, Image, Storage, Expense, Sale

# Files to be removed (eBay-related)
EBAY_FILES = [
    'app/atv/ebay.py',
    'app/atv/ebay_analytics.py',
    'app/atv/ebay_api.py',
    'app/atv/ebay_dashboard.py',
    'app/atv/ebay_forms.py',
    'app/atv/ebay_routes.py',
    'app/atv/ebay_settings.py',
    'app/config/ebay_templates.py',
    'app/static/js/ebay_price_suggestions.js',
    'app/templates/atv/ebay_analytics.html',
    'app/templates/atv/ebay_settings.html',
    'app/templates/atv/ebay_templates.html'
]

# Function to clean up unnecessary files
def remove_unnecessary_files():
    base_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    for file_path in EBAY_FILES:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"Removing file: {full_path}")
            os.remove(full_path)
        else:
            print(f"File not found: {full_path}")
            
def update_imports():
    """Update __init__.py files to remove eBay imports"""
    # Update app/atv/__init__.py to remove eBay blueprint
    atv_init = Path('app/atv/__init__.py').absolute()
    
    if atv_init.exists():
        with open(atv_init, 'r') as f:
            content = f.read()
            
        # Remove eBay-related blueprint registrations
        new_content = content
        lines_to_remove = [
            "from app.atv import ebay_routes",
            "from app.atv import ebay_dashboard",
            "from app.atv import ebay_analytics",
            "from app.atv import ebay_settings"
        ]
        
        for line in lines_to_remove:
            new_content = new_content.replace(line, "# " + line + " # Removed by simplify_app.py")
            
        with open(atv_init, 'w') as f:
            f.write(new_content)
            
        print("Updated app/atv/__init__.py to remove eBay imports")

def main():
    """Main function to run all simplification steps"""
    print("Starting app simplification...")
    
    # Remove unnecessary files
    remove_unnecessary_files()
    
    # Update imports
    update_imports()
    
    print("App simplification complete!")

if __name__ == "__main__":
    main()
