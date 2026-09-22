"""add category customization

Revision ID: 20260922_0005
Revises: 20260922_0004
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260922_0005"
down_revision: Union[str, Sequence[str], None] = "20260922_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("color", sa.String(7), nullable=False, server_default="#6AA57D"))
    op.add_column("categories", sa.Column("icon", sa.String(40), nullable=False, server_default="tag"))


def downgrade() -> None:
    op.drop_column("categories", "icon")
    op.drop_column("categories", "color")