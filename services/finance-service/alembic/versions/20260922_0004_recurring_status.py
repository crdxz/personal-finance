"""add recurring status

Revision ID: 20260922_0004
Revises: 20260922_0003
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260922_0004"
down_revision: Union[str, Sequence[str], None] = "20260922_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recurring_transactions", sa.Column("status", sa.String(12), nullable=False, server_default="active"))


def downgrade() -> None:
    op.drop_column("recurring_transactions", "status")