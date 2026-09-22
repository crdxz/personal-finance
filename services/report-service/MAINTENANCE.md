# Report Service Maintenance Guide

## Responsibility

Report Service is read-only. It calculates COP financial metrics from the tables owned by Finance Service:

- `financial_accounts`
- `categories`
- `transactions`
- `budgets`
- `recurring_transactions`

It never creates, updates or deletes financial records. Auth Service remains responsible for users and JWT issuance.

## Setup and execution

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8002
python -m pytest
```

The service must use the same `DATABASE_URL` and `SECRET_KEY` as Finance/Auth Services. Reports are scoped to `user_id` extracted from the JWT; never add a user id as a trusted query parameter.

## Report design

`GET /api/v1/reports/dashboard` is the frontend aggregate endpoint. It returns:

- Overview cards: income, expenses, net result, savings rate, counts, average/largest expense and recurring monthly estimate.
- Account cards: balance and percentage of total balance.
- Category charts: income/expense amount, percentage, count and average.
- Cash-flow series: daily, weekly or monthly income, expenses, net and cumulative net.
- Budget progress: limit, spent, remaining, percentage used and status.
- Recurring obligations: next run and normalized monthly estimate.
- Recent transactions: suitable for activity tables.
- Insights: savings, negative balance, top expense category and budget warnings.

Specialized endpoints return individual widgets for lazy loading:

```text
GET /api/v1/reports/overview
GET /api/v1/reports/cash-flow?granularity=day|week|month
GET /api/v1/reports/expenses/by-category
GET /api/v1/reports/income/by-category
GET /api/v1/reports/accounts
GET /api/v1/reports/budgets
GET /api/v1/reports/recurring
GET /api/v1/reports/recent-transactions
GET /api/v1/reports/insights
```

Most endpoints accept `start` and `end` in `YYYY-MM-DD` format. All values are COP and all calculations ignore transactions with `deleted_at` set.

## Metric rules

- `net = income - expenses`.
- `savings_rate = net / income * 100`; zero when income is zero.
- Transfers are excluded because Finance Service stores them with type `transfer`.
- Budget status: `on_track` below 80%, `near_limit` from 80% through 100%, `over_limit` above 100%.
- Weekly recurring amounts are normalized as `amount * 52 / 12`; yearly amounts as `amount / 12`; monthly amounts unchanged.
- Money is quantized to two decimals with `Decimal`, never binary floating point.

## Performance and security

- Keep report queries read-only and scoped by `user_id`.
- Add indexes before introducing new high-cardinality filters.
- For large datasets, introduce materialized daily/monthly aggregates rather than loading all transactions into Python.
- Keep RLS enabled on Finance tables; the service's backend database role must be the only role with direct read access.
- Never expose `password_hash`, database credentials or JWT secrets in report responses.

## Troubleshooting

- `401`: JWT missing, expired or signed with a different `SECRET_KEY`.
- `503`: check `DATABASE_URL` and database availability.
- Empty dashboard: verify the selected date range and that Finance Service has COP transactions for the authenticated user.
- Incorrect totals: check `deleted_at`, transaction type and transfer handling.
