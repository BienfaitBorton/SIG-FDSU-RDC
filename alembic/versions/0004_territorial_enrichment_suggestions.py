"""add territorial enrichment suggestions

Revision ID: 0004_territorial_enrichment
Revises: 0003_decision_profiles
Create Date: 2026-07-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0004_territorial_enrichment"
down_revision = "0003_decision_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "territorial_enrichment_suggestions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("entity_name", sa.String(length=250), nullable=True),
        sa.Column("field_name", sa.String(length=120), nullable=False),
        sa.Column("proposed_value", sa.Text(), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("consulted_at", sa.DateTime(), nullable=False),
        sa.Column("confidence_level", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="proposé"),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("validated_by", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_territorial_enrichment_entity",
        "territorial_enrichment_suggestions",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_territorial_enrichment_field",
        "territorial_enrichment_suggestions",
        ["field_name"],
    )
    op.create_index(
        "ix_territorial_enrichment_status",
        "territorial_enrichment_suggestions",
        ["status"],
    )
    op.create_index(
        "ix_territorial_enrichment_source",
        "territorial_enrichment_suggestions",
        ["source_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_territorial_enrichment_source", table_name="territorial_enrichment_suggestions")
    op.drop_index("ix_territorial_enrichment_status", table_name="territorial_enrichment_suggestions")
    op.drop_index("ix_territorial_enrichment_field", table_name="territorial_enrichment_suggestions")
    op.drop_index("ix_territorial_enrichment_entity", table_name="territorial_enrichment_suggestions")
    op.drop_table("territorial_enrichment_suggestions")
