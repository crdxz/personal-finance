"""create users table

Revision ID: 20260921_0001
Revises:
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260921_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY")
    op.execute(
        "REVOKE ALL ON TABLE public.alembic_version FROM anon, authenticated"
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.execute("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE public.users FROM anon, authenticated")


def downgrade() -> None:
    op.execute("ALTER TABLE public.users DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")
