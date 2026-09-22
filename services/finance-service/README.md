# Finance Service

Source of truth for personal finance accounts, categories, income, expenses, transfers and monthly summaries.

This service owns the complete personal-finance movement domain and is maintained independently from Auth, Budget and Report services.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set `DATABASE_URL` to the same PostgreSQL/Supabase connection used by the Auth Service, and `SECRET_KEY` to the same JWT secret.

Apply the schema to Supabase from this directory:

```powershell
python -m alembic upgrade head
```

## Run

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

## Endpoints

- `GET /health`
- `POST /api/v1/finance/accounts`
- `GET /api/v1/finance/accounts`
- `POST /api/v1/finance/categories`
- `GET /api/v1/finance/categories`
- `POST /api/v1/finance/transactions`
- `GET /api/v1/finance/transactions?start=2026-01-01&end=2026-01-31`
- `PATCH /api/v1/finance/transactions/{id}`
- `DELETE /api/v1/finance/transactions/{id}` (anulación lógica)
- `POST /api/v1/finance/transfers`
- `GET /api/v1/finance/summary/monthly?year=2026&month=1`
- `POST /api/v1/finance/budgets`
- `GET /api/v1/finance/budgets`
- `GET /api/v1/finance/reports/by-category?year=2026&month=1`
- `POST /api/v1/finance/recurring`
- `GET /api/v1/finance/recurring`
- `POST /api/v1/finance/recurring/{id}/run`

Every finance endpoint requires `Authorization: Bearer <auth-service-token>`.

All monetary values use Colombian pesos (`COP`). Other currencies are rejected intentionally. Transaction creation accepts `Idempotency-Key` to prevent duplicates when a client retries a request.
