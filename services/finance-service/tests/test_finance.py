from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_current_user_id
from app.database.base import Base
from app.database.session import get_db
from app.main import app


test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_user_id() -> int:
    return 7


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_user_id
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "finance-service"


def test_account_income_expense_and_summary() -> None:
    account = client.post("/api/v1/finance/accounts", json={"name": "Cuenta principal", "type": "bank", "currency": "COP", "initial_balance": "100000"})
    assert account.status_code == 201
    account_id = account.json()["id"]

    income = client.post("/api/v1/finance/transactions", json={"account_id": account_id, "type": "income", "amount": "500000", "currency": "COP", "transaction_date": "2026-09-01"})
    expense = client.post("/api/v1/finance/transactions", json={"account_id": account_id, "type": "expense", "amount": "125000", "currency": "COP", "transaction_date": "2026-09-02"})

    assert income.status_code == 201
    assert expense.status_code == 201
    assert client.get("/api/v1/finance/accounts").json()[0]["balance"] == "475000.00"
    summary = client.get("/api/v1/finance/summary/monthly?year=2026&month=9")
    assert summary.json()["income"] == "500000.00"
    assert summary.json()["expenses"] == "125000.00"
    assert summary.json()["balance"] == "375000.00"


def test_transfer_moves_balance_between_accounts() -> None:
    source = client.post("/api/v1/finance/accounts", json={"name": "Origen", "type": "bank", "initial_balance": "1000"}).json()
    destination = client.post("/api/v1/finance/accounts", json={"name": "Destino", "type": "cash", "initial_balance": "0"}).json()
    response = client.post("/api/v1/finance/transfers", json={"source_account_id": source["id"], "destination_account_id": destination["id"], "amount": "250", "transaction_date": str(date.today())})

    assert response.status_code == 201
    balances = {account["name"]: account["balance"] for account in client.get("/api/v1/finance/accounts").json()}
    assert balances["Origen"] == "750.00"
    assert balances["Destino"] == "250.00"


def test_endpoints_require_authentication() -> None:
    app.dependency_overrides.pop(get_current_user_id)
    response = client.get("/api/v1/finance/accounts")
    assert response.status_code == 401
    app.dependency_overrides[get_current_user_id] = override_user_id


def test_transaction_uses_default_account_when_account_is_omitted() -> None:
    before = next(
        account["balance"]
        for account in client.get("/api/v1/finance/accounts").json()
        if account["name"] == "Cuenta principal"
    )
    response = client.post(
        "/api/v1/finance/transactions",
        json={
            "type": "expense",
            "amount": "12500",
            "currency": "COP",
            "transaction_date": "2026-09-22",
            "description": "Transporte",
        },
    )

    assert response.status_code == 201
    account = client.get("/api/v1/finance/accounts").json()[0]
    assert account["name"] == "Cuenta principal"
    assert float(before) - float(account["balance"]) == 12500


def test_recurring_income_uses_default_account_when_account_is_omitted() -> None:
    response = client.post(
        "/api/v1/finance/recurring",
        json={
            "type": "income",
            "amount": "2500000",
            "recurrence_rule": "biweekly",
            "next_run": "2026-10-01",
            "description": "Salario",
        },
    )

    assert response.status_code == 201
    assert response.json()["recurrence_rule"] == "biweekly"


def test_categories_include_defaults_and_support_crud_customization() -> None:
    categories = client.get("/api/v1/finance/categories")
    assert categories.status_code == 200
    assert any(item["name"] == "Alimentación" and item["color"] for item in categories.json())

    created = client.post("/api/v1/finance/categories", json={"name": "Mascotas", "type": "expense", "color": "#123456", "icon": "paw"})
    assert created.status_code == 201
    category_id = created.json()["id"]
    assert created.json()["color"] == "#123456"
    assert created.json()["icon"] == "paw"

    updated = client.patch(f"/api/v1/finance/categories/{category_id}", json={"name": "Mascotas y hogar", "color": "#654321"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Mascotas y hogar"
    assert updated.json()["color"] == "#654321"

    deleted = client.delete(f"/api/v1/finance/categories/{category_id}")
    assert deleted.status_code == 204


def test_fixed_expense_template_runs_with_actual_invoice_amount() -> None:
    category = client.post("/api/v1/finance/categories", json={"name": "Servicios", "type": "expense"}).json()
    recurring = client.post("/api/v1/finance/recurring", json={"category_id": category["id"], "type": "expense", "amount": "120000", "recurrence_rule": "monthly", "next_run": "2026-10-01", "description": "Internet"})

    assert recurring.status_code == 201
    run = client.post(f"/api/v1/finance/recurring/{recurring.json()['id']}/run", json={"amount": "137500"})

    assert run.status_code == 201
    assert run.json()["type"] == "expense"
    assert run.json()["amount"] == "137500.00"


def test_debt_progress_and_estimated_completion_date() -> None:
    debt = client.post("/api/v1/finance/debts", json={"name": "Crédito educativo", "total_amount": "1000000", "monthly_payment": "250000", "start_date": "2026-09-01"})
    assert debt.status_code == 201
    assert debt.json()["progress_percentage"] == "0.00"
    assert debt.json()["remaining_amount"] == "1000000.00"
    assert debt.json()["estimated_end_date"] == "2026-12-01"

    payment = client.post(f"/api/v1/finance/debts/{debt.json()['id']}/payments", json={"amount": "250000", "payment_date": "2026-09-22", "note": "Abono mensual"})
    assert payment.status_code == 200
    assert payment.json()["paid_amount"] == "250000.00"
    assert payment.json()["progress_percentage"] == "25.00"

    final = client.post(f"/api/v1/finance/debts/{debt.json()['id']}/payments", json={"amount": "750000", "payment_date": "2026-12-01"})
    assert final.status_code == 200
    assert final.json()["status"] == "paid"
    assert final.json()["remaining_amount"] == "0.00"


def test_cop_is_the_only_supported_currency() -> None:
    response = client.post("/api/v1/finance/accounts", json={"name": "Dólares", "type": "bank", "currency": "USD"})
    assert response.status_code == 422


def test_idempotency_does_not_duplicate_a_transaction() -> None:
    account = client.post("/api/v1/finance/accounts", json={"name": "Idempotencia", "type": "cash", "initial_balance": "0"}).json()
    payload = {"account_id": account["id"], "type": "income", "amount": "10000", "transaction_date": "2026-09-10"}
    first = client.post("/api/v1/finance/transactions", json=payload, headers={"Idempotency-Key": "income-unique-1"})
    second = client.post("/api/v1/finance/transactions", json=payload, headers={"Idempotency-Key": "income-unique-1"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    balances = {item["name"]: item["balance"] for item in client.get("/api/v1/finance/accounts").json()}
    assert balances["Idempotencia"] == "10000.00"


def test_budget_report_recurring_update_delete_and_pagination() -> None:
    category = client.post("/api/v1/finance/categories", json={"name": "Alimentación", "type": "expense"}).json()
    account = client.post("/api/v1/finance/accounts", json={"name": "Presupuesto", "type": "bank", "initial_balance": "500000"}).json()
    transaction = client.post("/api/v1/finance/transactions", json={"account_id": account["id"], "category_id": category["id"], "type": "expense", "amount": "50000", "transaction_date": "2026-09-12"}).json()

    budget = client.post("/api/v1/finance/budgets", json={"category_id": category["id"], "year": 2026, "month": 9, "amount": "100000"})
    report = client.get("/api/v1/finance/reports/by-category?year=2026&month=9")
    income_category = client.post("/api/v1/finance/categories", json={"name": "Salario", "type": "income"}).json()
    recurring = client.post("/api/v1/finance/recurring", json={"account_id": account["id"], "category_id": income_category["id"], "type": "income", "amount": "25000", "recurrence_rule": "monthly", "next_run": "2026-10-01"})
    recurring_run = client.post(f"/api/v1/finance/recurring/{recurring.json()['id']}/run")
    updated = client.patch(f"/api/v1/finance/transactions/{transaction['id']}", json={"description": "Mercado"})
    page = client.get("/api/v1/finance/transactions?page=1&page_size=2")
    deleted = client.delete(f"/api/v1/finance/transactions/{transaction['id']}")

    assert budget.status_code == 201
    assert budget.json()["spent"] == "50000.00"
    assert report.status_code == 200
    assert any(item["category_name"] == "Alimentación" for item in report.json())
    assert recurring.status_code == 201
    assert recurring_run.status_code == 201
    assert updated.status_code == 200
    assert page.status_code == 200 and page.json()["page_size"] == 2
    assert deleted.status_code == 204
