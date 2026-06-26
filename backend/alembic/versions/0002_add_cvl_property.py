"""Add cvl_property column to findings

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("cvl_property", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "cvl_property")
