from datetime import date

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id
from app.database.session import get_db
from app.schemas.finance import (
    AccountCreate,
    AccountResponse,
    CategoryCreate,
    CategoryResponse,
    MonthlySummary,
    BudgetCreate,
    BudgetResponse,
    CategoryReport,
    RecurringCreate,
    RecurringResponse,
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
    TransactionUpdate,
    TransferCreate,
)
from app.services.finance_service import FinanceService

router = APIRouter(prefix="/finance", tags=["finance"])


def get_service(db: Session = Depends(get_db)) -> FinanceService:
    return FinanceService(db)


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(request: AccountCreate, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> AccountResponse:
    return service.create_account(user_id, request)


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[AccountResponse]:
    return service.repository.accounts(user_id)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(request: CategoryCreate, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> CategoryResponse:
    return service.create_category(user_id, request)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[CategoryResponse]:
    return service.repository.categories(user_id)


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(request: TransactionCreate, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> TransactionResponse:
    return service.create_transaction(user_id, request, idempotency_key)


@router.get("/transactions", response_model=TransactionPage)
def list_transactions(start: date | None = Query(default=None), end: date | None = Query(default=None), page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> TransactionPage:
    items, total = service.repository.transactions(user_id, start, end, page, page_size)
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, request: TransactionUpdate, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> TransactionResponse:
    return service.update_transaction(user_id, transaction_id, request)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> Response:
    service.delete_transaction(user_id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/transfers", response_model=list[TransactionResponse], status_code=status.HTTP_201_CREATED)
def create_transfer(request: TransferCreate, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[TransactionResponse]:
    return list(service.create_transfer(user_id, request))


@router.get("/summary/monthly", response_model=MonthlySummary)
def monthly_summary(year: int = Query(ge=2000, le=2100), month: int = Query(ge=1, le=12), user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> MonthlySummary:
    return MonthlySummary(**service.monthly_summary(user_id, year, month))


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(request: BudgetCreate, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> BudgetResponse:
    return BudgetResponse(**service.budget_response(service.create_budget(user_id, request)))


@router.get("/budgets", response_model=list[BudgetResponse])
def list_budgets(user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[BudgetResponse]:
    return [BudgetResponse(**service.budget_response(budget)) for budget in service.repository.budgets(user_id)]


@router.get("/reports/by-category", response_model=list[CategoryReport])
def category_report(year: int = Query(ge=2000, le=2100), month: int = Query(ge=1, le=12), user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[CategoryReport]:
    return [CategoryReport(**item) for item in service.category_report(user_id, year, month)]


@router.post("/recurring", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED)
def create_recurring(request: RecurringCreate, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> RecurringResponse:
    return service.create_recurring(user_id, request)


@router.get("/recurring", response_model=list[RecurringResponse])
def list_recurring(user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[RecurringResponse]:
    return service.repository.recurring(user_id)


@router.post("/recurring/{recurring_id}/run", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def run_recurring(recurring_id: int, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> TransactionResponse:
    return service.run_recurring(user_id, recurring_id)


@router.post("/recurring/{recurring_id}/pause", response_model=RecurringResponse)
def pause_recurring(recurring_id: int, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> RecurringResponse:
    return service.set_recurring_status(user_id, recurring_id, "paused")


@router.post("/recurring/{recurring_id}/resume", response_model=RecurringResponse)
def resume_recurring(recurring_id: int, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> RecurringResponse:
    return service.set_recurring_status(user_id, recurring_id, "active")


@router.post("/recurring/{recurring_id}/cancel", response_model=RecurringResponse)
def cancel_recurring(recurring_id: int, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> RecurringResponse:
    return service.set_recurring_status(user_id, recurring_id, "cancelled")


@router.post("/recurring/process-due", response_model=list[TransactionResponse])
def process_due_recurring(today: date | None = None, user_id: int = Depends(get_current_user_id), service: FinanceService = Depends(get_service)) -> list[TransactionResponse]:
    return service.process_due_recurring(user_id, today or date.today())
