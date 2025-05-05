"""
Add hours tracking fields to ATV model
"""
from alembic import op
import sqlalchemy as sa
import sys
import os

def upgrade():
    # Add hours tracking columns to ATV table
    op.add_column('atv', sa.Column('acquisition_hours', sa.Float, nullable=True))
    op.add_column('atv', sa.Column('repair_hours', sa.Float, nullable=True))
    op.add_column('atv', sa.Column('selling_hours', sa.Float, nullable=True))
    op.add_column('atv', sa.Column('total_hours', sa.Float, nullable=True))

def downgrade():
    # Remove the columns if needed
    op.drop_column('atv', 'acquisition_hours')
    op.drop_column('atv', 'repair_hours')
    op.drop_column('atv', 'selling_hours')
    op.drop_column('atv', 'total_hours')

if __name__ == '__main__':
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the parent directory to sys.path
    parent_dir = os.path.dirname(script_dir)
    sys.path.insert(0, parent_dir)
    
    # Import app objects
    from app import create_app, db
    
    # Create app context
    app = create_app()
    with app.app_context():
        # Run the upgrade
        upgrade()
        print("Migration successful! Added hours tracking fields to ATV model.")
