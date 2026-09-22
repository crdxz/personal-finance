# Finance Service Maintenance Guide

## Purpose

Finance Service is the source of truth for personal financial activity. It owns accounts, categories, income, expenses, transfers, budgets, recurring movements and financial summaries.

Auth Service owns users and JWT issuance. Finance Service validates the JWT signature using the same `SECRET_KEY`; it does not store passwords. Budget Service owns planning rules, and Report Service owns read-heavy analytics.

## Local setup

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Required environment variables:

```text
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<the same JWT secret configured in auth-service>
CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
```

The default database is SQLite for isolated tests. Never commit `.env` or database passwords.

## Run and verify

```powershell
python -m uvicorn app.main:app --reload --port 8001
python -m pytest
```

Swagger is available at `http://127.0.0.1:8001/docs`.

## Database migrations

The Finance Service uses its own Alembic version table, `public.finance_alembic_version`, because Auth Service shares the same PostgreSQL database but has a separate migration history.

```powershell
python -m alembic upgrade head
python -m alembic current
```

Migration rules:

1. Create a new revision; never edit a migration already applied to Supabase.
2. Add RLS and revoke `anon`/`authenticated` access for every new public table.
3. Use `NUMERIC(14, 2)` for money and keep the currency as `COP`.
4. Test the upgrade SQL before applying it remotely.
5. Test downgrade logic where a rollback is required.

## Domain rules

- Every record is scoped by `user_id` from the JWT, never from a request body.
- Amounts are positive; movement type determines whether the account balance increases or decreases.
- Transfers create paired movements and are not income or expense.
- Transactions are annulled logically with `deleted_at`.
- `Idempotency-Key` prevents duplicate transaction creation after client retries.
- Recurring definitions are executed through `POST /api/v1/finance/recurring/{id}/run`.
- Transfer records cannot be edited or deleted individually.

## Endpoint groups

- `/api/v1/finance/accounts`: financial accounts and balances.
- `/api/v1/finance/categories`: income and expense categories.
- `/api/v1/finance/transactions`: movements, filters, pagination and lifecycle.
- `/api/v1/finance/transfers`: account-to-account transfers.
- `/api/v1/finance/budgets`: monthly category limits.
- `/api/v1/finance/recurring`: recurring movement definitions and execution.
- `/api/v1/finance/summary/monthly`: monthly totals.
- `/api/v1/finance/reports/by-category`: expense aggregation by category.

All protected routes require `Authorization: Bearer <token>` from Auth Service.

## Troubleshooting

- `401`: check the Bearer token and that both services use the same `SECRET_KEY`.
- `422`: verify `COP`, positive amounts, valid dates and category type.
- `503`: check `DATABASE_URL`, PostgreSQL connectivity and migration state.
- Duplicate records: send a stable `Idempotency-Key` on transaction creation.
- RLS warnings: verify `rowsecurity = true` for all Finance Service tables in `pg_tables`.
