# Architecture

## Architecture style

Microservices

## Services

- Auth Service
- Budget Service
- Finance Service (implemented in `services/finance-service`)
- Report Service

## Finance Service ownership

The Finance Service is the source of truth for a person's financial activity:

- Financial accounts and balances
- Income and expense categories
- Income and expense transactions
- Transfers between accounts
- Monthly financial summaries

Budget Service owns limits and planning. Report Service consumes financial data for projections and analytics. User identity remains owned by Auth Service; Finance Service uses the Auth Service JWT and never stores passwords.

## Report Service ownership

Report Service is a read-only analytics layer. It does not duplicate financial writes. It reads Finance Service tables and provides dashboard metrics, time series, category/account breakdowns, budget progress, recurring obligations, recent activity and actionable insights. The aggregate endpoint is `GET /api/v1/reports/dashboard`; specialized widget endpoints are available for lazy loading.
