"""add site_history table, lifecycle enum and site fields

Revision ID: 0002_sites_history
Revises: 0001_nb_sites_reference
Create Date: 2026-07-01 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_sites_history'
down_revision = '0001_nb_sites_reference'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    site_columns = {column["name"] for column in inspector.get_columns("sites")}

    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE site_lifecycle AS ENUM ('Prevu', 'Planifie', 'En construction', 'Actif', 'Hors service');
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
        """
    )

    if "programme" not in site_columns:
        op.add_column('sites', sa.Column('programme', sa.String(length=200), nullable=True))
    if "annee_planification" not in site_columns:
        op.add_column('sites', sa.Column('annee_planification', sa.Integer(), nullable=True))
    if "phase" not in site_columns:
        op.add_column('sites', sa.Column('phase', sa.String(length=100), nullable=True))
    if "priorite" not in site_columns:
        op.add_column('sites', sa.Column('priorite', sa.Integer(), nullable=False, server_default=sa.text('0')))

    if not inspector.has_table("site_history"):
        op.create_table(
            'site_history',
            sa.Column('id', sa.BigInteger(), primary_key=True),
            sa.Column('site_id', sa.BigInteger(), sa.ForeignKey('sites.id', ondelete='CASCADE'), nullable=False),
            sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('changed_by', sa.String(length=200), nullable=True),
            sa.Column('action', sa.String(length=50), nullable=True),
            sa.Column('data', sa.JSON(), nullable=True),
        )

    if "statut" in site_columns:
        op.execute(
            "ALTER TABLE sites ALTER COLUMN statut TYPE site_lifecycle USING (\n"
            "CASE WHEN statut = 'En etude' THEN 'Planifie'\n"
            "WHEN statut = 'Prevu' THEN 'Prevu'\n"
            "WHEN statut = 'En construction' THEN 'En construction'\n"
            "WHEN statut = 'Actif' THEN 'Actif'\n"
            "WHEN statut = 'Hors service' THEN 'Hors service'\n"
            "ELSE 'Prevu' END)::site_lifecycle"
        )

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
