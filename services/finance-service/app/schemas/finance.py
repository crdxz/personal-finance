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


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    user_id: int | None
    is_active: bool


class TransactionCreate(BaseModel):
    account_id: int
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
    account_id: int
    category_id: int | None = None
    type: MovementType
    amount: Decimal = Field(gt=0, decimal_places=2)
    recurrence_rule: Literal["weekly", "monthly", "yearly"]
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
