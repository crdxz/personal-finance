from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DateRange(BaseModel):
    start: date
    end: date
    currency: Literal["COP"] = "COP"


class OverviewMetrics(BaseModel):
    income: Decimal
    expenses: Decimal
    net: Decimal
    savings_rate: Decimal
    expense_count: int
    income_count: int
    transaction_count: int
    average_expense: Decimal
    largest_expense: Decimal
    recurring_monthly_estimate: Decimal


class AccountMetric(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: str
    balance: Decimal
    percentage_of_total: Decimal


class CategoryMetric(BaseModel):
    category_id: int | None
    category_name: str
    amount: Decimal
    percentage: Decimal
    transaction_count: int
    average: Decimal


class TimeSeriesPoint(BaseModel):
    period: str
    income: Decimal
    expenses: Decimal
    net: Decimal
    cumulative_net: Decimal


class BudgetMetric(BaseModel):
    id: int
    category_id: int
    category_name: str
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: Decimal
    status: Literal["on_track", "near_limit", "over_limit"]


class RecurringMetric(BaseModel):
    id: int
    type: str
    amount: Decimal
    recurrence_rule: str
    next_run: date
    description: str | None
    monthly_estimate: Decimal


class RecentTransaction(BaseModel):
    id: int
    date: date
    type: str
    amount: Decimal
    description: str | None
    account_name: str
    category_name: str


class Insight(BaseModel):
    code: str
    severity: Literal["info", "warning", "success"]
    title: str
    message: str
    value: Decimal | None = None


class DashboardReport(BaseModel):
    period: DateRange
    overview: OverviewMetrics
    accounts: list[AccountMetric]
    expenses_by_category: list[CategoryMetric]
    income_by_category: list[CategoryMetric]
    cash_flow: list[TimeSeriesPoint]
    budgets: list[BudgetMetric]
    recurring: list[RecurringMetric]
    recent_transactions: list[RecentTransaction]
    insights: list[Insight]


class HealthResponse(BaseModel):
    status: str
    service: str
