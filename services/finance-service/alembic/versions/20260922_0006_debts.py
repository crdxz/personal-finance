"""add debts and payments

Revision ID: 20260922_0006
Revises: 20260922_0005
Create Date: 2026-09-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260922_0006"
down_revision: Union[str, Sequence[str], None] = "20260922_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("debts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("total_amount", sa.Numeric(14, 2), nullable=False), sa.Column("paid_amount", sa.Numeric(14, 2), nullable=False, server_default="0"), sa.Column("monthly_payment", sa.Numeric(14, 2), nullable=True), sa.Column("start_date", sa.Date(), nullable=False), sa.Column("due_date", sa.Date(), nullable=True), sa.Column("status", sa.String(12), nullable=False, server_default="active"), sa.Column("notes", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_debts_user_id", "debts", ["user_id"])
    op.create_table("debt_payments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("debt_id", sa.Integer(), sa.ForeignKey("debts.id"), nullable=False), sa.Column("amount", sa.Numeric(14, 2), nullable=False), sa.Column("payment_date", sa.Date(), nullable=False), sa.Column("note", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_debt_payments_user_id", "debt_payments", ["user_id"])
    op.create_index("ix_debt_payments_debt_id", "debt_payments", ["debt_id"])
    for table in ("debts", "debt_payments"):
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE public.{table} FROM anon, authenticated")


def downgrade() -> None:
    op.execute("ALTER TABLE public.debt_payments DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.debts DISABLE ROW LEVEL SECURITY")
    op.drop_table("debt_payments")
    op.drop_table("debts")