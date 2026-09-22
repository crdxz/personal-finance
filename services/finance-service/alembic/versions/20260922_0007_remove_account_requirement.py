"""remove account requirement

Revision ID: 20260922_0007
Revises: 20260922_0006
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op

revision: str = "20260922_0007"
down_revision: Union[str, Sequence[str], None] = "20260922_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("transactions", "account_id", nullable=True)
    op.alter_column("recurring_transactions", "account_id", nullable=True)


def downgrade() -> None:
    op.alter_column("recurring_transactions", "account_id", nullable=False)
    op.alter_column("transactions", "account_id", nullable=False)