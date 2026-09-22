from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("financial_accounts.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="COP")
    recurrence_rule: Mapped[str] = mapped_column(String(20))
    next_run: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(12), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
