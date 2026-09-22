"""protect finance alembic version table

Revision ID: 20260922_0002
Revises: 20260922_0001
Create Date: 2026-09-22
"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260922_0002"
down_revision: Union[str, Sequence[str], None] = "20260922_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.finance_alembic_version ENABLE ROW LEVEL SECURITY")
    op.execute(
        "REVOKE ALL ON TABLE public.finance_alembic_version FROM anon, authenticated"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE public.finance_alembic_version DISABLE ROW LEVEL SECURITY")