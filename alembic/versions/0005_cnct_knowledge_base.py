"""add cnct knowledge base tables

Revision ID: 0005_cnct_knowledge_base
Revises: 0004_territorial_enrichment
Create Date: 2026-07-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_cnct_knowledge_base"
down_revision = "0004_territorial_enrichment"
branch_labels = None
depends_on = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    ]


def upgrade() -> None:
    op.create_table(
        "territorial_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("field_name", sa.String(length=120), nullable=True),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=200), nullable=True),
        sa.Column("source_date", sa.Date(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("confidence_level", sa.String(length=40), nullable=False, server_default="à vérifier"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="proposé"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        *_audit_columns(),
    )
    op.create_index("ix_territorial_sources_entity", "territorial_sources", ["entity_type", "entity_id"])
    op.create_index("ix_territorial_sources_field", "territorial_sources", ["field_name"])
    op.create_index("ix_territorial_sources_status", "territorial_sources", ["status"])

    op.create_table(
        "territorial_documents",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("entity_name", sa.String(length=250), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("document_type", sa.String(length=80), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), sa.ForeignKey("territorial_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="proposé"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        *_audit_columns(),
    )
    op.create_index("ix_territorial_documents_entity", "territorial_documents", ["entity_type", "entity_id"])
    op.create_index("ix_territorial_documents_status", "territorial_documents", ["status"])

    op.create_table(
        "territorial_statistics",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("indicator_name", sa.String(length=160), nullable=False),
        sa.Column("indicator_value", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("source_id", sa.BigInteger(), sa.ForeignKey("territorial_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="proposé"),
        *_audit_columns(),
    )
    op.create_index("ix_territorial_statistics_entity", "territorial_statistics", ["entity_type", "entity_id"])
    op.create_index("ix_territorial_statistics_indicator", "territorial_statistics", ["indicator_name"])

    op.create_table(
        "territorial_history",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), sa.ForeignKey("territorial_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="proposé"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_territorial_history_entity", "territorial_history", ["entity_type", "entity_id"])
    op.create_index("ix_territorial_history_event", "territorial_history", ["event_type"])

    op.create_table(
        "territorial_quality",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("dimension", sa.String(length=120), nullable=False),
        sa.Column("score", sa.Numeric(6, 2), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="à compléter"),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_territorial_quality_entity", "territorial_quality", ["entity_type", "entity_id"])
    op.create_index("ix_territorial_quality_dimension", "territorial_quality", ["dimension"])

    op.create_table(
        "territorial_completeness",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("entity_name", sa.String(length=250), nullable=True),
        sa.Column("section_name", sa.String(length=120), nullable=False),
        sa.Column("completeness_rate", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("missing_fields_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("priority", sa.String(length=40), nullable=False, server_default="normale"),
        sa.Column("last_updated_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_territorial_completeness_entity", "territorial_completeness", ["entity_type", "entity_id"])
    op.create_index("ix_territorial_completeness_section", "territorial_completeness", ["section_name"])
    op.create_index("ix_territorial_completeness_priority", "territorial_completeness", ["priority"])


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_territorial_completeness_priority", "territorial_completeness"),
        ("ix_territorial_completeness_section", "territorial_completeness"),
        ("ix_territorial_completeness_entity", "territorial_completeness"),
        ("ix_territorial_quality_dimension", "territorial_quality"),
        ("ix_territorial_quality_entity", "territorial_quality"),
        ("ix_territorial_history_event", "territorial_history"),
        ("ix_territorial_history_entity", "territorial_history"),
        ("ix_territorial_statistics_indicator", "territorial_statistics"),
        ("ix_territorial_statistics_entity", "territorial_statistics"),
        ("ix_territorial_documents_status", "territorial_documents"),
        ("ix_territorial_documents_entity", "territorial_documents"),
        ("ix_territorial_sources_status", "territorial_sources"),
        ("ix_territorial_sources_field", "territorial_sources"),
        ("ix_territorial_sources_entity", "territorial_sources"),
    ]:
        op.drop_index(index_name, table_name=table_name)
    for table_name in [
        "territorial_completeness",
        "territorial_quality",
        "territorial_history",
        "territorial_statistics",
        "territorial_documents",
        "territorial_sources",
    ]:
        op.drop_table(table_name)
