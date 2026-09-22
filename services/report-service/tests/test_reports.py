from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user_id
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models.finance import Account, Budget, Category, RecurringTransaction, Transaction

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


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


def test_cors_preflight_is_handled_before_authentication() -> None:
    response = client.options(
        "/api/v1/reports/dashboard",
        headers={
            "Origin": "https://personal-finance-pi-jet.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://personal-finance-pi-jet.vercel.app"
    assert "GET" in response.headers["access-control-allow-methods"]
    assert "Authorization" in response.headers["access-control-allow-headers"]


def seed_data() -> None:
    db = TestingSessionLocal()
    food = Category(id=1, user_id=7, name="Alimentación", type="expense", is_active=True)
    salary = Category(id=2, user_id=7, name="Salario", type="income", is_active=True)
    account = Account(id=1, user_id=7, name="Cuenta principal", type="bank", currency="COP", balance=Decimal("850000"), is_active=True)
    db.add_all([food, salary, account])
    db.add_all([
        Transaction(user_id=7, account_id=1, category_id=2, type="income", amount=Decimal("1000000"), currency="COP", transaction_date=date(2026, 9, 1), is_recurring=False),
        Transaction(user_id=7, account_id=1, category_id=1, type="expense", amount=Decimal("150000"), currency="COP", transaction_date=date(2026, 9, 2), is_recurring=False),
        Transaction(user_id=7, account_id=1, category_id=1, type="expense", amount=Decimal("50000"), currency="COP", transaction_date=date(2026, 9, 10), is_recurring=False),
    ])
    db.add(Budget(id=1, user_id=7, category_id=1, year=2026, month=9, amount=Decimal("250000"), currency="COP"))
    db.add(RecurringTransaction(id=1, user_id=7, account_id=1, category_id=1, type="expense", amount=Decimal("30000"), currency="COP", recurrence_rule="monthly", next_run=date(2026, 10, 1), description="Arriendo", is_active=True))
    db.commit()
    db.close()


def test_dashboard_contains_frontend_metrics() -> None:
    seed_data()
    response = client.get("/api/v1/reports/dashboard?start=2026-09-01&end=2026-09-30&granularity=day")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overview"]["income"] == "1000000.00"
    assert payload["overview"]["expenses"] == "200000.00"
    assert payload["overview"]["net"] == "800000.00"
    assert payload["overview"]["savings_rate"] == "80.00"
    assert payload["expenses_by_category"][0]["percentage"] == "100.00"
    assert payload["budgets"][0]["percentage_used"] == "80.00"
    assert payload["recurring"][0]["monthly_estimate"] == "30000.00"
    assert len(payload["cash_flow"]) == 3
    assert payload["recent_transactions"][0]["amount"] == "50000.00"
    assert payload["insights"]


def test_specialized_report_endpoints() -> None:
    response = client.get("/api/v1/reports/overview?start=2026-09-01&end=2026-09-30")
    categories = client.get("/api/v1/reports/expenses/by-category?start=2026-09-01&end=2026-09-30")
    cash_flow = client.get("/api/v1/reports/cash-flow?start=2026-09-01&end=2026-09-30&granularity=month")
    budgets = client.get("/api/v1/reports/budgets?start=2026-09-01&end=2026-09-30")

    assert response.status_code == categories.status_code == cash_flow.status_code == budgets.status_code == 200
    assert categories.json()[0]["category_name"] == "Alimentación"
    assert cash_flow.json()[0]["net"] == "800000.00"
    assert budgets.json()[0]["remaining"] == "50000.00"


def test_reports_require_authentication() -> None:
    app.dependency_overrides.pop(get_current_user_id)
    response = client.get("/api/v1/reports/dashboard")
    assert response.status_code == 401
    app.dependency_overrides[get_current_user_id] = override_user_id
