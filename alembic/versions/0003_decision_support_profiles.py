"""add decision support profile tables

Revision ID: 0003_decision_profiles
Revises: 0002_sites_history
Create Date: 2026-07-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_decision_profiles"
down_revision = "0002_sites_history"
branch_labels = None
depends_on = None


def _profile_keys(localite_table: str) -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("localite_id", sa.BigInteger(), sa.ForeignKey(f"{localite_table}.id", ondelete="CASCADE"), nullable=True),
        sa.Column("territoire_id", sa.BigInteger(), sa.ForeignKey("territoires.id", ondelete="CASCADE"), nullable=True),
    ]


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    ]


def _indexes(table_name: str, priority: bool = False) -> None:
    op.create_index(f"ix_{table_name}_localite_id", table_name, ["localite_id"])
    op.create_index(f"ix_{table_name}_territoire_id", table_name, ["territoire_id"])
    if priority:
        op.create_index("ix_fdsu_priority_scores_priorite", table_name, ["score_priorite_fdsu"])


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    localite_table = "localites" if inspector.has_table("localites") else "villages"

    op.create_table(
        "territorial_profiles",
        *_profile_keys(localite_table),
        sa.Column("population", sa.BigInteger(), nullable=True),
        sa.Column("niveau_enclavement", sa.String(length=80), nullable=True),
        *_audit_columns(),
    )
    _indexes("territorial_profiles")

    op.create_table(
        "connectivity_profiles",
        *_profile_keys(localite_table),
        sa.Column("couverture_2g", sa.Boolean(), nullable=True),
        sa.Column("couverture_3g", sa.Boolean(), nullable=True),
        sa.Column("couverture_4g", sa.Boolean(), nullable=True),
        sa.Column("couverture_5g", sa.Boolean(), nullable=True),
        sa.Column("score_connectivite", sa.Numeric(6, 2), nullable=True),
        *_audit_columns(),
    )
    _indexes("connectivity_profiles")

    op.create_table(
        "public_services",
        *_profile_keys(localite_table),
        sa.Column("centre_sante", sa.Boolean(), nullable=True),
        sa.Column("ecole_primaire", sa.Boolean(), nullable=True),
        sa.Column("ecole_secondaire", sa.Boolean(), nullable=True),
        sa.Column("marche", sa.Boolean(), nullable=True),
        sa.Column("electricite", sa.Boolean(), nullable=True),
        *_audit_columns(),
    )
    _indexes("public_services")

    op.create_table(
        "economic_activities",
        *_profile_keys(localite_table),
        sa.Column("activite_principale", sa.String(length=200), nullable=True),
        sa.Column("activite_secondaire", sa.String(length=200), nullable=True),
        sa.Column("potentiel_agricole", sa.String(length=80), nullable=True),
        sa.Column("potentiel_minier", sa.String(length=80), nullable=True),
        sa.Column("potentiel_commercial", sa.String(length=80), nullable=True),
        sa.Column("potentiel_numerique", sa.String(length=80), nullable=True),
        sa.Column("score_potentiel", sa.Numeric(6, 2), nullable=True),
        *_audit_columns(),
    )
    _indexes("economic_activities")

    op.create_table(
        "development_challenges",
        *_profile_keys(localite_table),
        sa.Column("niveau_enclavement", sa.String(length=80), nullable=True),
        sa.Column("defis", sa.Text(), nullable=True),
        *_audit_columns(),
    )
    _indexes("development_challenges")

    op.create_table(
        "fdsu_priority_scores",
        *_profile_keys(localite_table),
        sa.Column("score_connectivite", sa.Numeric(6, 2), nullable=True),
        sa.Column("score_potentiel", sa.Numeric(6, 2), nullable=True),
        sa.Column("score_priorite_fdsu", sa.Numeric(6, 2), nullable=True),
        sa.Column("recommandation", sa.Text(), nullable=True),
        *_audit_columns(),
    )
    _indexes("fdsu_priority_scores", priority=True)


def downgrade() -> None:
    op.drop_index("ix_fdsu_priority_scores_priorite", table_name="fdsu_priority_scores")
    for table_name in [
        "fdsu_priority_scores",
        "development_challenges",
        "economic_activities",
        "public_services",
        "connectivity_profiles",
        "territorial_profiles",
    ]:
        op.drop_index(f"ix_{table_name}_territoire_id", table_name=table_name)
        op.drop_index(f"ix_{table_name}_localite_id", table_name=table_name)
        op.drop_table(table_name)
