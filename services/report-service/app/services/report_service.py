from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import Account, Budget, Category, RecurringTransaction, Transaction
from app.schemas.reports import (
    AccountMetric,
    BudgetMetric,
    CategoryMetric,
    DashboardReport,
    DateRange,
    Insight,
    OverviewMetrics,
    RecentTransaction,
    RecurringMetric,
    TimeSeriesPoint,
)

ZERO = Decimal("0.00")
HUNDRED = Decimal("100")


def money(value: Decimal | int | float | None) -> Decimal:
    return (Decimal(str(value or 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def percentage(value: Decimal, total: Decimal) -> Decimal:
    return money((value / total * HUNDRED) if total else ZERO)


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _transactions(self, user_id: int, period: DateRange) -> list[Transaction]:
        statement = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.currency == "COP",
            Transaction.deleted_at.is_(None),
            Transaction.transaction_date >= period.start,
            Transaction.transaction_date <= period.end,
        ).order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        return list(self.db.scalars(statement))

    def _accounts(self, user_id: int) -> list[Account]:
        return list(self.db.scalars(select(Account).where(Account.user_id == user_id, Account.is_active.is_(True)).order_by(Account.name)))

    def _categories(self, user_id: int) -> dict[int, str]:
        categories = self.db.scalars(select(Category).where(Category.is_active.is_(True), (Category.user_id == user_id) | (Category.user_id.is_(None))))
        return {category.id: category.name for category in categories}

    def overview(self, transactions: list[Transaction], user_id: int, period: DateRange) -> OverviewMetrics:
        incomes = [transaction for transaction in transactions if transaction.type == "income"]
        expenses = [transaction for transaction in transactions if transaction.type == "expense"]
        income = money(sum((transaction.amount for transaction in incomes), ZERO))
        expense_total = money(sum((transaction.amount for transaction in expenses), ZERO))
        recurring = self.db.scalars(select(RecurringTransaction).where(RecurringTransaction.user_id == user_id, RecurringTransaction.is_active.is_(True), RecurringTransaction.currency == "COP"))
        recurring_monthly = ZERO
        for item in recurring:
            if item.recurrence_rule == "weekly":
                recurring_monthly += item.amount * Decimal("52") / Decimal("12")
            elif item.recurrence_rule == "yearly":
                recurring_monthly += item.amount / Decimal("12")
            else:
                recurring_monthly += item.amount
        return OverviewMetrics(
            income=income,
            expenses=expense_total,
            net=money(income - expense_total),
            savings_rate=percentage(income - expense_total, income),
            expense_count=len(expenses),
            income_count=len(incomes),
            transaction_count=len(transactions),
            average_expense=money(expense_total / len(expenses)) if expenses else ZERO,
            largest_expense=money(max((transaction.amount for transaction in expenses), default=ZERO)),
            recurring_monthly_estimate=money(recurring_monthly),
        )

    def by_category(self, transactions: list[Transaction], categories: dict[int, str], movement_type: str) -> list[CategoryMetric]:
        grouped: dict[int | None, list[Transaction]] = defaultdict(list)
        for transaction in transactions:
            if transaction.type == movement_type:
                grouped[transaction.category_id].append(transaction)
        total = money(sum((transaction.amount for values in grouped.values() for transaction in values), ZERO))
        result = []
        for category_id, values in grouped.items():
            amount = money(sum((transaction.amount for transaction in values), ZERO))
            result.append(CategoryMetric(category_id=category_id, category_name=categories.get(category_id, "Sin categoría"), amount=amount, percentage=percentage(amount, total), transaction_count=len(values), average=money(amount / len(values))))
        return sorted(result, key=lambda item: item.amount, reverse=True)

    def cash_flow(self, transactions: list[Transaction], granularity: str) -> list[TimeSeriesPoint]:
        grouped: dict[str, tuple[Decimal, Decimal]] = defaultdict(lambda: (ZERO, ZERO))
        for transaction in transactions:
            if granularity == "day":
                period = transaction.transaction_date.isoformat()
            elif granularity == "week":
                period = (transaction.transaction_date - timedelta(days=transaction.transaction_date.weekday())).isoformat()
            else:
                period = transaction.transaction_date.strftime("%Y-%m")
            income, expenses = grouped[period]
            if transaction.type == "income":
                income += transaction.amount
            elif transaction.type == "expense":
                expenses += transaction.amount
            grouped[period] = (income, expenses)
        cumulative = ZERO
        result = []
        for period in sorted(grouped):
            income, expenses = grouped[period]
            net = money(income - expenses)
            cumulative = money(cumulative + net)
            result.append(TimeSeriesPoint(period=period, income=money(income), expenses=money(expenses), net=net, cumulative_net=cumulative))
        return result

    def budgets(self, user_id: int, period: DateRange, transactions: list[Transaction], categories: dict[int, str]) -> list[BudgetMetric]:
        budgets = self.db.scalars(select(Budget).where(Budget.user_id == user_id, Budget.currency == "COP"))
        result = []
        for budget in budgets:
            budget_start = date(budget.year, budget.month, 1)
            if budget_start < period.start.replace(day=1) or budget_start > period.end.replace(day=1):
                continue
            spent = money(sum((transaction.amount for transaction in transactions if transaction.type == "expense" and transaction.category_id == budget.category_id and transaction.transaction_date.year == budget.year and transaction.transaction_date.month == budget.month), ZERO))
            used = percentage(spent, budget.amount)
            status = "over_limit" if spent > budget.amount else "near_limit" if used >= 80 else "on_track"
            result.append(BudgetMetric(id=budget.id, category_id=budget.category_id, category_name=categories.get(budget.category_id, "Sin categoría"), limit=money(budget.amount), spent=spent, remaining=money(budget.amount - spent), percentage_used=used, status=status))
        return result

    def recurring(self, user_id: int) -> list[RecurringMetric]:
        recurring = self.db.scalars(select(RecurringTransaction).where(RecurringTransaction.user_id == user_id, RecurringTransaction.is_active.is_(True), RecurringTransaction.currency == "COP").order_by(RecurringTransaction.next_run))
        result = []
        for item in recurring:
            multiplier = Decimal("52") / Decimal("12") if item.recurrence_rule == "weekly" else Decimal("1") / Decimal("12") if item.recurrence_rule == "yearly" else Decimal("1")
            result.append(RecurringMetric(id=item.id, type=item.type, amount=money(item.amount), recurrence_rule=item.recurrence_rule, next_run=item.next_run, description=item.description, monthly_estimate=money(item.amount * multiplier)))
        return result

    def recent(self, transactions: list[Transaction], accounts: dict[int, str], categories: dict[int, str], limit: int) -> list[RecentTransaction]:
        return [RecentTransaction(id=item.id, date=item.transaction_date, type=item.type, amount=money(item.amount), description=item.description, account_name=accounts.get(item.account_id, "Cuenta desconocida"), category_name=categories.get(item.category_id, "Sin categoría")) for item in transactions[:limit]]

    def insights(self, overview: OverviewMetrics, categories: list[CategoryMetric], budgets: list[BudgetMetric]) -> list[Insight]:
        result: list[Insight] = []
        if overview.income == ZERO:
            result.append(Insight(code="no_income", severity="warning", title="Sin ingresos registrados", message="Registra tus ingresos para calcular tu capacidad de ahorro."))
        elif overview.savings_rate >= 20:
            result.append(Insight(code="healthy_savings", severity="success", title="Buen nivel de ahorro", message="Tu ahorro está por encima del 20% de tus ingresos.", value=overview.savings_rate))
        elif overview.savings_rate < 0:
            result.append(Insight(code="negative_balance", severity="warning", title="Gastas más de lo que ingresas", message="Revisa tus gastos para recuperar un balance positivo.", value=overview.net))
        else:
            result.append(Insight(code="low_savings", severity="info", title="Ahorro por fortalecer", message="Tu margen de ahorro está por debajo del 20%.", value=overview.savings_rate))
        if categories:
            top = categories[0]
            result.append(Insight(code="top_category", severity="info", title="Mayor categoría de gasto", message=f"{top.category_name} concentra la mayor parte de tus gastos.", value=top.amount))
        for budget in budgets:
            if budget.status == "over_limit":
                result.append(Insight(code=f"budget_{budget.id}_over", severity="warning", title="Presupuesto excedido", message=f"Superaste el presupuesto de {budget.category_name}.", value=budget.remaining))
        return result

    def dashboard(self, user_id: int, period: DateRange, granularity: str = "month", recent_limit: int = 10) -> DashboardReport:
        transactions = self._transactions(user_id, period)
        categories = self._categories(user_id)
        accounts = self._accounts(user_id)
        account_map = {account.id: account.name for account in accounts}
        overview = self.overview(transactions, user_id, period)
        expenses = self.by_category(transactions, categories, "expense")
        incomes = self.by_category(transactions, categories, "income")
        budgets = self.budgets(user_id, period, transactions, categories)
        account_total = money(sum((account.balance for account in accounts), ZERO))
        account_metrics = [AccountMetric(id=account.id, name=account.name, type=account.type, balance=money(account.balance), percentage_of_total=percentage(account.balance, account_total)) for account in accounts]
        insight_list = self.insights(overview, expenses, budgets)
        return DashboardReport(period=period, overview=overview, accounts=account_metrics, expenses_by_category=expenses, income_by_category=incomes, cash_flow=self.cash_flow(transactions, granularity), budgets=budgets, recurring=self.recurring(user_id), recent_transactions=self.recent(transactions, account_map, categories, recent_limit), insights=insight_list)
