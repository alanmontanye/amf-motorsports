#!/bin/bash
# This script runs during the build process on Render

# Install dependencies
pip install -r requirements.txt

# Initialize database if running in production
if [ "$FLASK_CONFIG" = "production" ]; then
  echo "Running database migrations and initialization..."
  python db_migration_utils.py migrate || echo "Migration ran with issues, but continuing..."
  python initialize_db.py --sample || echo "Sample data initialization ran with issues, but continuing..."
fi

echo "Build process completed!"
