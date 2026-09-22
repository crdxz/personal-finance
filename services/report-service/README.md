# Report Service

Read-only analytics microservice for the Personal Finance platform. It reads Finance Service tables and exposes metrics ready for dashboards, charts, cards and alerts. It never writes financial data.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure the same `DATABASE_URL` and `SECRET_KEY` used by Finance Service/Auth Service. The service uses Colombian pesos (`COP`).

## Run

```powershell
python -m uvicorn app.main:app --reload --port 8002
```

Swagger: `http://127.0.0.1:8002/docs`

## Endpoint catalog

- `GET /health`
- `GET /api/v1/reports/dashboard`: complete dashboard payload.
- `GET /api/v1/reports/overview`: income, expenses, net, savings rate, averages and recurring estimate.
- `GET /api/v1/reports/cash-flow`: daily, weekly or monthly time series.
- `GET /api/v1/reports/expenses/by-category`: expense ranking and percentages.
- `GET /api/v1/reports/income/by-category`: income distribution.
- `GET /api/v1/reports/accounts`: balances and portfolio percentages.
- `GET /api/v1/reports/budgets`: limit usage and status.
- `GET /api/v1/reports/recurring`: recurring obligations and monthly estimates.
- `GET /api/v1/reports/recent-transactions`: recent movement cards.
- `GET /api/v1/reports/insights`: savings, negative balance and budget alerts.

Most report endpoints accept `start=YYYY-MM-DD` and `end=YYYY-MM-DD`. All protected endpoints require `Authorization: Bearer <auth-service-token>`.
