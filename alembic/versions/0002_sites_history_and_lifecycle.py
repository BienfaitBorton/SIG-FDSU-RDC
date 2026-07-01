"""add site_history table, lifecycle enum and site fields

Revision ID: 0002_sites_history_and_lifecycle
Revises: 0001_add_nb_sites_reference_to_territoires
Create Date: 2026-07-01 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_sites_history_and_lifecycle'
down_revision = '0001_add_nb_sites_reference_to_territoires'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create new ENUM type for lifecycle
    op.execute("CREATE TYPE site_lifecycle AS ENUM ('Prévu', 'Planifié', 'En construction', 'Actif', 'Hors service')")

    # Add new columns to sites
    op.add_column('sites', sa.Column('programme', sa.String(length=200), nullable=True))
    op.add_column('sites', sa.Column('annee_planification', sa.Integer(), nullable=True))
    op.add_column('sites', sa.Column('phase', sa.String(length=100), nullable=True))
    op.add_column('sites', sa.Column('priorite', sa.Integer(), nullable=False, server_default=sa.text('0')))

    # Create site_history table
    op.create_table(
        'site_history',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('site_id', sa.BigInteger(), sa.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('changed_by', sa.String(length=200), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
    )

    # Alter existing statut column from old enum to new site_lifecycle
    # Map old values to new roughly: 'En étude' -> 'Planifié'
    op.execute(
        "ALTER TABLE sites ALTER COLUMN statut TYPE site_lifecycle USING (\n"
        "CASE WHEN statut = 'En étude' THEN 'Planifié'\n"
        "WHEN statut = 'Prévu' THEN 'Prévu'\n"
        "WHEN statut = 'En construction' THEN 'En construction'\n"
        "WHEN statut = 'Actif' THEN 'Actif'\n"
        "WHEN statut = 'Hors service' THEN 'Hors service'\n"
        "ELSE 'Prévu' END)::site_lifecycle"
    )

    # Drop old enum type if exists
    op.execute("DROP TYPE IF EXISTS site_status")


def downgrade() -> None:
    # Recreate old enum
    op.execute("CREATE TYPE site_status AS ENUM ('Prévu', 'En étude', 'En construction', 'Actif', 'Hors service')")

    # Alter statut back to old enum, mapping Planifié -> En étude
    op.execute(
        "ALTER TABLE sites ALTER COLUMN statut TYPE site_status USING (\n"
        "CASE WHEN statut = 'Planifié' THEN 'En étude'\n"
        "WHEN statut = 'Prévu' THEN 'Prévu'\n"
        "WHEN statut = 'En construction' THEN 'En construction'\n"
        "WHEN statut = 'Actif' THEN 'Actif'\n"
        "WHEN statut = 'Hors service' THEN 'Hors service'\n"
        "ELSE 'Prévu' END)::site_status"
    )

    # Drop site_history table
    op.drop_table('site_history')

    # Drop new columns from sites
    op.drop_column('sites', 'priorite')
    op.drop_column('sites', 'phase')
    op.drop_column('sites', 'annee_planification')
    op.drop_column('sites', 'programme')

    # Drop new enum
    op.execute('DROP TYPE IF EXISTS site_lifecycle')
