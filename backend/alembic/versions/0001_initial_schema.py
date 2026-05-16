"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "repositories",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("github_url", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("owner", sa.String, nullable=False),
        sa.Column("last_ingested_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "scans",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("repository_id", sa.String, sa.ForeignKey("repositories.id"), nullable=True),
        sa.Column("pr_number", sa.Integer, nullable=True),
        sa.Column("pr_title", sa.String, nullable=True),
        sa.Column("filename", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("triggered_by", sa.String, nullable=False, server_default="manual"),
        sa.Column("critical_count", sa.Integer, server_default="0"),
        sa.Column("high_count", sa.Integer, server_default="0"),
        sa.Column("medium_count", sa.Integer, server_default="0"),
        sa.Column("low_count", sa.Integer, server_default="0"),
        sa.Column("info_count", sa.Integer, server_default="0"),
        sa.Column("node_latencies", sa.String, nullable=True),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("scan_id", sa.String, sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("severity", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("affected_lines", JSONB, nullable=False, server_default="[]"),
        sa.Column("affected_code", sa.Text, nullable=True),
        sa.Column("recommendation", sa.Text, nullable=False, server_default=""),
        sa.Column("exploit_scenario", sa.Text, nullable=False, server_default=""),
        sa.Column("test_stub", sa.Text, nullable=True),
        sa.Column("false_positive", sa.Boolean, server_default="false"),
        sa.Column("confidence", sa.String, nullable=False, server_default="MEDIUM"),
    )

    op.create_table(
        "vulnerability_embeddings",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("category", sa.String, nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_index("idx_findings_scan_id", "findings", ["scan_id"])
    op.create_index("idx_findings_severity", "findings", ["severity"])
    op.create_index("idx_scans_status", "scans", ["status"])
    op.create_index("idx_embeddings_source", "vulnerability_embeddings", ["source"])
    op.create_index("idx_embeddings_category", "vulnerability_embeddings", ["category"])


def downgrade() -> None:
    op.drop_table("vulnerability_embeddings")
    op.drop_table("findings")
    op.drop_table("scans")
    op.drop_table("repositories")
