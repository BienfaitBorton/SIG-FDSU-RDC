"""add nb_sites_reference to territoires

Revision ID: 0001_nb_sites_reference
Revises: 
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_nb_sites_reference'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nb_sites_reference column to territoires.

    This migration is written for PostgreSQL and will:
    - add a NOT NULL INTEGER column with DEFAULT 0,
      which ensures existing rows get 0.
    """
    op.add_column(
        'territoires',
        sa.Column('nb_sites_reference', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )


def downgrade() -> None:
    """Remove nb_sites_reference column from territoires."""
    op.drop_column('territoires', 'nb_sites_reference')
