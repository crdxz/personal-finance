from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, Budget, Category, Debt, DebtPayment, RecurringTransaction, Transaction
from app.repositories.finance_repository import FinanceRepository
from app.schemas.finance import AccountCreate, BudgetCreate, CategoryUpdate, DebtCreate, DebtPaymentCreate, RecurringCreate, TransactionCreate, TransactionUpdate, TransferCreate


class FinanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = FinanceRepository(db)

    def create_account(self, user_id: int, request: AccountCreate) -> Account:
        account = Account(user_id=user_id, name=request.name, type=request.type, currency="COP", balance=request.initial_balance)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def ensure_default_categories(self, user_id: int) -> None:
        if self.repository.user_categories(user_id):
            return
        defaults = [
            ("Salario", "income", "#31775A", "briefcase"),
            ("Otros ingresos", "income", "#6AA57D", "plus"),
            ("Vivienda", "expense", "#E76F51", "home"),
            ("Servicios", "expense", "#E5A94D", "bolt"),
            ("Alimentación", "expense", "#D65D40", "utensils"),
            ("Transporte", "expense", "#5A82A8", "car"),
            ("Ocio", "expense", "#8B6FA8", "sparkles"),
            ("Salud", "expense", "#B84D70", "heart"),
            ("Educación", "expense", "#527764", "book"),
            ("Otros gastos", "expense", "#78867E", "tag"),
        ]
        self.db.add_all([Category(user_id=user_id, name=name, type=category_type, color=color, icon=icon) for name, category_type, color, icon in defaults])
        self.db.commit()

    def update_category(self, user_id: int, category_id: int, request: CategoryUpdate) -> Category:
        category = self.repository.category_owned(user_id, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        for field in ("name", "color", "icon"):
            value = getattr(request, field)
            if value is not None:
                setattr(category, field, value)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, user_id: int, category_id: int) -> None:
        category = self.repository.category_owned(user_id, category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        category.is_active = False
        self.db.commit()

    def debt_response(self, debt: Debt) -> dict[str, object]:
        remaining = max(Decimal("0"), debt.total_amount - debt.paid_amount).quantize(Decimal("0.01"))
        progress = min(Decimal("100"), (debt.paid_amount / debt.total_amount * 100) if debt.total_amount else Decimal("0"))
        estimated_end = None
        if debt.monthly_payment and debt.monthly_payment > 0 and remaining > 0:
            months = int((remaining / debt.monthly_payment).to_integral_value(rounding="ROUND_CEILING"))
            estimated_end = debt.start_date.replace(day=1)
            for _ in range(max(0, months - 1)):
                next_month = estimated_end.month % 12 + 1
                next_year = estimated_end.year + (1 if estimated_end.month == 12 else 0)
                estimated_end = estimated_end.replace(year=next_year, month=next_month)
        return {"id": debt.id, "name": debt.name, "total_amount": debt.total_amount.quantize(Decimal("0.01")), "paid_amount": debt.paid_amount.quantize(Decimal("0.01")), "remaining_amount": remaining, "progress_percentage": progress.quantize(Decimal("0.01")), "estimated_end_date": estimated_end, "status": debt.status, "start_date": debt.start_date, "due_date": debt.due_date, "notes": debt.notes}

    def create_debt(self, user_id: int, request: DebtCreate) -> Debt:
        debt = Debt(user_id=user_id, name=request.name, total_amount=request.total_amount, monthly_payment=request.monthly_payment, start_date=request.start_date, due_date=request.due_date, notes=request.notes, status="active")
        self.db.add(debt)
        self.db.commit()
        self.db.refresh(debt)
        return debt

    def add_debt_payment(self, user_id: int, debt_id: int, request: DebtPaymentCreate) -> Debt:
        debt = self.repository.debt(user_id, debt_id)
        if not debt:
            raise HTTPException(status_code=404, detail="Debt not found")
        if debt.paid_amount + request.amount > debt.total_amount:
            raise HTTPException(status_code=422, detail="Payment exceeds remaining debt")
        self.db.add(DebtPayment(user_id=user_id, debt_id=debt.id, amount=request.amount, payment_date=request.payment_date, note=request.note))
        debt.paid_amount += request.amount
        if debt.paid_amount >= debt.total_amount:
            debt.status = "paid"
        self.db.commit()
        self.db.refresh(debt)
        return debt

    def create_transaction(self, user_id: int, request: TransactionCreate, idempotency_key: str | None = None) -> Transaction:
        if idempotency_key:
            existing = self.repository.idempotent_transaction(user_id, idempotency_key)
            if existing:
                return existing
        account = self.repository.default_account(user_id) if request.account_id is None else self.repository.account(user_id, request.account_id)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        category = self.repository.category(user_id, request.category_id) if request.category_id else None
        if request.category_id and not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        if category and category.type != request.type:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Category type must match transaction type")
        signed_amount = request.amount if request.type == "income" else -request.amount
        account.balance += signed_amount
        transaction = Transaction(user_id=user_id, account_id=account.id, category_id=request.category_id, type=request.type, amount=request.amount, currency="COP", description=request.description, transaction_date=request.transaction_date, idempotency_key=idempotency_key, is_recurring=request.is_recurring, recurrence_rule=request.recurrence_rule)
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def create_transfer(self, user_id: int, request: TransferCreate) -> tuple[Transaction, Transaction]:
        if request.source_account_id == request.destination_account_id:
            raise HTTPException(status_code=422, detail="Transfer accounts must be different")
        source = self.repository.account(user_id, request.source_account_id)
        destination = self.repository.account(user_id, request.destination_account_id)
        if not source or not destination:
            raise HTTPException(status_code=404, detail="Source or destination account not found")
        if source.balance < request.amount:
            raise HTTPException(status_code=422, detail="Insufficient account balance")
        transfer_id = uuid4()
        source.balance -= request.amount
        destination.balance += request.amount
        outgoing = Transaction(user_id=user_id, account_id=source.id, type="transfer", amount=request.amount, currency="COP", description=request.description, transaction_date=request.transaction_date, transfer_group_id=transfer_id)
        incoming = Transaction(user_id=user_id, account_id=destination.id, type="transfer", amount=request.amount, currency="COP", description=request.description, transaction_date=request.transaction_date, transfer_group_id=transfer_id)
        self.db.add_all([outgoing, incoming])
        self.db.commit()
        self.db.refresh(outgoing)
        self.db.refresh(incoming)
        return outgoing, incoming

    def monthly_summary(self, user_id: int, year: int, month: int) -> dict[str, object]:
        base = (Transaction.user_id == user_id, Transaction.deleted_at.is_(None), func.extract("year", Transaction.transaction_date) == year, func.extract("month", Transaction.transaction_date) == month)
        income = self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(*base, Transaction.type == "income")) or Decimal("0")
        expenses = self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(*base, Transaction.type == "expense")) or Decimal("0")
        return {"year": year, "month": month, "income": income, "expenses": expenses, "balance": income - expenses}

    def update_transaction(self, user_id: int, transaction_id: int, request: TransactionUpdate) -> Transaction:
        transaction = self.repository.transaction(user_id, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        if transaction.type == "transfer":
            raise HTTPException(status_code=422, detail="Transfers cannot be edited individually")
        if request.description is not None:
            transaction.description = request.description
        if request.transaction_date is not None:
            transaction.transaction_date = request.transaction_date
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete_transaction(self, user_id: int, transaction_id: int) -> None:
        transaction = self.repository.transaction(user_id, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        if transaction.type == "transfer":
            raise HTTPException(status_code=422, detail="Transfers cannot be deleted individually")
        account = self.repository.account(user_id, transaction.account_id)
        if account:
            account.balance -= transaction.amount if transaction.type == "income" else -transaction.amount
        transaction.deleted_at = datetime.now(timezone.utc)
        self.db.commit()

    def create_budget(self, user_id: int, request: BudgetCreate) -> Budget:
        category = self.repository.category(user_id, request.category_id)
        if not category or category.type != "expense":
            raise HTTPException(status_code=404, detail="Expense category not found")
        budget = Budget(user_id=user_id, category_id=request.category_id, year=request.year, month=request.month, amount=request.amount, currency="COP")
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def budget_response(self, budget: Budget) -> dict[str, object]:
        spent = self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.user_id == budget.user_id, Transaction.category_id == budget.category_id, Transaction.type == "expense", Transaction.deleted_at.is_(None), func.extract("year", Transaction.transaction_date) == budget.year, func.extract("month", Transaction.transaction_date) == budget.month)) or Decimal("0")
        return {"id": budget.id, "category_id": budget.category_id, "year": budget.year, "month": budget.month, "amount": budget.amount, "currency": "COP", "spent": spent, "remaining": budget.amount - spent}

    def category_report(self, user_id: int, year: int, month: int) -> list[dict[str, object]]:
        statement = select(Transaction.category_id, func.coalesce(Category.name, "Uncategorized"), func.sum(Transaction.amount)).join(Category, Category.id == Transaction.category_id, isouter=True).where(Transaction.user_id == user_id, Transaction.type == "expense", Transaction.deleted_at.is_(None), func.extract("year", Transaction.transaction_date) == year, func.extract("month", Transaction.transaction_date) == month).group_by(Transaction.category_id, Category.name).order_by(func.sum(Transaction.amount).desc())
        return [{"category_id": category_id, "category_name": name, "amount": amount} for category_id, name, amount in self.db.execute(statement).all()]

    def create_recurring(self, user_id: int, request: RecurringCreate) -> RecurringTransaction:
        account = self.repository.default_account(user_id) if request.account_id is None else self.repository.account(user_id, request.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        category = self.repository.category(user_id, request.category_id) if request.category_id else None
        if request.category_id and (not category or category.type != request.type):
            raise HTTPException(status_code=422, detail="Category type must match recurring transaction type")
        recurring = RecurringTransaction(user_id=user_id, account_id=account.id, category_id=request.category_id, type=request.type, amount=request.amount, currency="COP", recurrence_rule=request.recurrence_rule, next_run=request.next_run, description=request.description, status="active")
        self.db.add(recurring)
        self.db.commit()
        self.db.refresh(recurring)
        return recurring

    def run_recurring(self, user_id: int, recurring_id: int, actual_amount: Decimal | None = None) -> Transaction:
        recurring = self.db.scalar(select(RecurringTransaction).where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == user_id, RecurringTransaction.status == "active"))
        if not recurring:
            raise HTTPException(status_code=404, detail="Recurring transaction not found")
        transaction_request = TransactionCreate(account_id=recurring.account_id, category_id=recurring.category_id, type=recurring.type, amount=actual_amount or recurring.amount, currency="COP", description=recurring.description, transaction_date=recurring.next_run, is_recurring=True, recurrence_rule=recurring.recurrence_rule)
        transaction = self.create_transaction(user_id, transaction_request, f"recurring:{recurring.id}:{recurring.next_run.isoformat()}")
        if recurring.recurrence_rule == "biweekly":
            recurring.next_run += timedelta(days=14)
        else:
            next_month = recurring.next_run.month % 12 + 1
            next_year = recurring.next_run.year + (1 if recurring.next_run.month == 12 else 0)
            recurring.next_run = recurring.next_run.replace(year=next_year, month=next_month, day=min(recurring.next_run.day, monthrange(next_year, next_month)[1]))
        self.db.commit()
        return transaction

    def set_recurring_status(self, user_id: int, recurring_id: int, status_value: str) -> RecurringTransaction:
        recurring = self.db.scalar(select(RecurringTransaction).where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == user_id))
        if not recurring:
            raise HTTPException(status_code=404, detail="Recurring transaction not found")
        recurring.status = status_value
        recurring.is_active = status_value == "active"
        self.db.commit()
        self.db.refresh(recurring)
        return recurring

    def process_due_recurring(self, user_id: int, today: date) -> list[Transaction]:
        due = list(self.db.scalars(select(RecurringTransaction).where(RecurringTransaction.user_id == user_id, RecurringTransaction.status == "active", RecurringTransaction.next_run <= today)))
        return [self.run_recurring(user_id, item.id) for item in due]
