from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Budget, Category, Debt, RecurringTransaction, Transaction


class FinanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def categories(self, user_id: int) -> list[Category]:
        statement = select(Category).where(Category.is_active.is_(True), (Category.user_id == user_id) | (Category.user_id.is_(None))).order_by(Category.name)
        return list(self.db.scalars(statement))

    def user_categories(self, user_id: int) -> list[Category]:
        return list(self.db.scalars(select(Category).where(Category.user_id == user_id, Category.is_active.is_(True)).order_by(Category.name)))

    def category_owned(self, user_id: int, category_id: int) -> Category | None:
        return self.db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user_id, Category.is_active.is_(True)))

    def category(self, user_id: int, category_id: int) -> Category | None:
        return self.db.scalar(select(Category).where(Category.id == category_id, Category.is_active.is_(True), (Category.user_id == user_id) | (Category.user_id.is_(None))))

    def transactions(self, user_id: int, start: date | None = None, end: date | None = None, page: int = 1, page_size: int = 20) -> tuple[list[Transaction], int]:
        statement = select(Transaction).where(Transaction.user_id == user_id, Transaction.deleted_at.is_(None))
        if start:
            statement = statement.where(Transaction.transaction_date >= start)
        if end:
            statement = statement.where(Transaction.transaction_date <= end)
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = list(self.db.scalars(statement.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).offset((page - 1) * page_size).limit(page_size)))
        return items, total

    def transaction(self, user_id: int, transaction_id: int) -> Transaction | None:
        return self.db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id, Transaction.deleted_at.is_(None)))

    def idempotent_transaction(self, user_id: int, key: str) -> Transaction | None:
        return self.db.scalar(select(Transaction).where(Transaction.user_id == user_id, Transaction.idempotency_key == key, Transaction.deleted_at.is_(None)))

    def budget(self, user_id: int, budget_id: int) -> Budget | None:
        return self.db.scalar(select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id))

    def budgets(self, user_id: int) -> list[Budget]:
        return list(self.db.scalars(select(Budget).where(Budget.user_id == user_id).order_by(Budget.year.desc(), Budget.month.desc())))

    def recurring(self, user_id: int) -> list[RecurringTransaction]:
        return list(self.db.scalars(select(RecurringTransaction).where(RecurringTransaction.user_id == user_id, RecurringTransaction.is_active.is_(True)).order_by(RecurringTransaction.next_run)))

    def debt(self, user_id: int, debt_id: int) -> Debt | None:
        return self.db.scalar(select(Debt).where(Debt.id == debt_id, Debt.user_id == user_id))

    def debts(self, user_id: int) -> list[Debt]:
        return list(self.db.scalars(select(Debt).where(Debt.user_id == user_id, Debt.status == "active").order_by(Debt.created_at.desc())))

    def commit(self) -> None:
        self.db.commit()
        self.db.flush()
