from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


AccountType = Literal["cash", "bank", "savings", "credit_card", "digital_wallet"]
MovementType = Literal["income", "expense"]
CategoryType = Literal["income", "expense"]


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType
    currency: Literal["COP"] = "COP"
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    currency: str
    balance: Decimal
    is_active: bool


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: CategoryType
    color: str = Field(default="#6AA57D", pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="tag", min_length=1, max_length=40)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    user_id: int | None
    is_active: bool
    color: str
    icon: str


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(default=None, min_length=1, max_length=40)


class DebtCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    total_amount: Decimal = Field(gt=0, decimal_places=2)
    monthly_payment: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    start_date: date
    due_date: date | None = None
    notes: str | None = Field(default=None, max_length=500)


class DebtPaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    payment_date: date
    note: str | None = Field(default=None, max_length=500)


class DebtResponse(BaseModel):
    id: int
    name: str
    total_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    progress_percentage: Decimal
    estimated_end_date: date | None
    status: str
    start_date: date
    due_date: date | None
    notes: str | None


class TransactionCreate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    type: MovementType
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Literal["COP"] = "COP"
    description: str | None = Field(default=None, max_length=500)
    transaction_date: date
    is_recurring: bool = False
    recurrence_rule: Literal["weekly", "monthly", "yearly"] | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    type: str
    amount: Decimal
    currency: str
    description: str | None
    transaction_date: date
    transfer_group_id: UUID | None


class TransferCreate(BaseModel):
    source_account_id: int
    destination_account_id: int
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Literal["COP"] = "COP"
    description: str | None = Field(default=None, max_length=500)
    transaction_date: date


class MonthlySummary(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    balance: Decimal


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    transaction_date: date | None = None


class BudgetCreate(BaseModel):
    category_id: int
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Literal["COP"] = "COP"


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    year: int
    month: int
    amount: Decimal
    currency: str
    spent: Decimal
    remaining: Decimal


class CategoryReport(BaseModel):
    category_id: int | None
    category_name: str
    amount: Decimal


class RecurringCreate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    type: MovementType
    amount: Decimal = Field(gt=0, decimal_places=2)
    recurrence_rule: Literal["biweekly", "monthly"]
    next_run: date
    description: str | None = Field(default=None, max_length=500)


class RecurringResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    type: str
    amount: Decimal
    currency: str
    recurrence_rule: str
    next_run: date
    description: str | None
    is_active: bool
    status: Literal["active", "paused", "cancelled"]


class RecurringRunRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
