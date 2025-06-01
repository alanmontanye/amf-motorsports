"""Add parting out fields

This migration adds new fields to support the enhanced parting-out workflow.
It adds fields to the ATV and Part models without disrupting existing data.

Revision ID: 89add453ac12
Revises: (put the ID of your latest migration here)
Create Date: 2023-06-01 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import uuid


# revision identifiers, used by Alembic
revision = '89add453ac12'
down_revision = None  # Update this to your current latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create a table reference for updates
    atv_table = table('atv',
        column('id', sa.Integer),
        column('parting_status', sa.String(20)),
        column('machine_id', sa.String(64))
    )
    
    # Add parting_status column to ATV
    op.add_column('atv', sa.Column('parting_status', sa.String(20), server_default='whole'))
    
    # Add machine_id column to ATV
    op.add_column('atv', sa.Column('machine_id', sa.String(64)))
    
    # Initialize machine_id for all existing ATVs
    connection = op.get_bind()
    atvs = connection.execute('SELECT id FROM atv').fetchall()
    
    for atv_id in atvs:
        connection.execute(
            atv_table.update().
            where(atv_table.c.id == atv_id[0]).
            values(machine_id=str(uuid.uuid4()))
        )
    
    # Add tote column to Part
    op.add_column('part', sa.Column('tote', sa.String(20)))
    
    # Add estimated_value column to Part
    op.add_column('part', sa.Column('estimated_value', sa.Float))
    
    # Add listing_id column to Part
    op.add_column('part', sa.Column('listing_id', sa.String(128)))
    
    # Add listing_date column to Part
    op.add_column('part', sa.Column('listing_date', sa.DateTime))


def downgrade():
    # Remove new Part columns
    op.drop_column('part', 'listing_date')
    op.drop_column('part', 'listing_id')
    op.drop_column('part', 'estimated_value')
    op.drop_column('part', 'tote')
    
    # Remove new ATV columns
    op.drop_column('atv', 'machine_id')
    op.drop_column('atv', 'parting_status')
