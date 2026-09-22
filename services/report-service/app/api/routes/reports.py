from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id
from app.database.session import get_db
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
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


def resolve_period(start: date | None, end: date | None) -> DateRange:
    today = date.today()
    period_start = start or today.replace(day=1)
    period_end = end or today
    if period_end < period_start:
        raise HTTPException(status_code=422, detail="end must be greater than or equal to start")
    return DateRange(start=period_start, end=period_end)


@router.get("/dashboard", response_model=DashboardReport)
def dashboard(start: date | None = None, end: date | None = None, granularity: Literal["day", "week", "month"] = "month", recent_limit: int = Query(default=10, ge=1, le=50), user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> DashboardReport:
    return service.dashboard(user_id, resolve_period(start, end), granularity, recent_limit)


@router.get("/overview", response_model=OverviewMetrics)
def overview(start: date | None = None, end: date | None = None, user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> OverviewMetrics:
    period = resolve_period(start, end)
    transactions = service._transactions(user_id, period)
    return service.overview(transactions, user_id, period)


@router.get("/cash-flow", response_model=list[TimeSeriesPoint])
def cash_flow(start: date | None = None, end: date | None = None, granularity: Literal["day", "week", "month"] = "month", user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[TimeSeriesPoint]:
    period = resolve_period(start, end)
    return service.cash_flow(service._transactions(user_id, period), granularity)


@router.get("/expenses/by-category", response_model=list[CategoryMetric])
def expenses_by_category(start: date | None = None, end: date | None = None, user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[CategoryMetric]:
    period = resolve_period(start, end)
    return service.by_category(service._transactions(user_id, period), service._categories(user_id), "expense")


@router.get("/income/by-category", response_model=list[CategoryMetric])
def income_by_category(start: date | None = None, end: date | None = None, user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[CategoryMetric]:
    period = resolve_period(start, end)
    return service.by_category(service._transactions(user_id, period), service._categories(user_id), "income")


@router.get("/accounts", response_model=list[AccountMetric])
def accounts(user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[AccountMetric]:
    report = service.dashboard(user_id, resolve_period(None, None))
    return report.accounts


@router.get("/budgets", response_model=list[BudgetMetric])
def budgets(start: date | None = None, end: date | None = None, user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[BudgetMetric]:
    period = resolve_period(start, end)
    transactions = service._transactions(user_id, period)
    return service.budgets(user_id, period, transactions, service._categories(user_id))


@router.get("/recurring", response_model=list[RecurringMetric])
def recurring(user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[RecurringMetric]:
    return service.recurring(user_id)


@router.get("/recent-transactions", response_model=list[RecentTransaction])
def recent_transactions(limit: int = Query(default=10, ge=1, le=50), user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[RecentTransaction]:
    report = service.dashboard(user_id, resolve_period(None, None), recent_limit=limit)
    return report.recent_transactions


@router.get("/insights", response_model=list[Insight])
def insights(start: date | None = None, end: date | None = None, user_id: int = Depends(get_current_user_id), service: ReportService = Depends(get_service)) -> list[Insight]:
    period = resolve_period(start, end)
    transactions = service._transactions(user_id, period)
    categories = service._categories(user_id)
    overview = service.overview(transactions, user_id, period)
    expenses = service.by_category(transactions, categories, "expense")
    budgets = service.budgets(user_id, period, transactions, categories)
    return service.insights(overview, expenses, budgets)
