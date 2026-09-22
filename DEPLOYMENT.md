# Deployment separation

## Vercel-only deployment

Deploy this monorepo as four independent Vercel projects. Supabase remains the shared PostgreSQL database.

| Vercel project | Root Directory | Framework | Entrypoint |
|---|---|---|---|
| `personal-finance-frontend` | `frontend` | Other | static `index.html` |
| `personal-finance-auth` | `services/auth-service` | FastAPI | `main:app` |
| `personal-finance-finance` | `services/finance-service` | FastAPI | `main:app` |
| `personal-finance-report` | `services/report-service` | FastAPI | `main:app` |

Create the four projects from the same GitHub repository. In each Vercel project, set the corresponding **Root Directory** before deploying. Do not deploy the repository root as one project.

### Backend environment variables

Set these in Auth, Finance and Report projects:

```text
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<the-same-strong-secret-in-all-three-services>
CORS_ORIGINS=https://personal-finance-frontend.vercel.app
```

`DATABASE_URL` and `SECRET_KEY` must never be added to frontend files or committed to Git.

### Frontend configuration

After the three backend projects have their public URLs, update `frontend/config.js` and deploy the frontend:

```javascript
window.APP_CONFIG = {
  AUTH_API_URL: "https://personal-finance-auth.vercel.app/api/v1",
  FINANCE_API_URL: "https://personal-finance-finance.vercel.app/api/v1",
  REPORT_API_URL: "https://personal-finance-report.vercel.app/api/v1",
};
```

These are public API URLs, not secrets. Update `CORS_ORIGINS` in all backend projects with the final frontend URL, then redeploy the backends.

### Vercel settings for Python services

Vercel detects FastAPI from `requirements.txt` and the `[tool.vercel]` entrypoint in each service `pyproject.toml`. Each service also contains a root `main.py` that exposes `main:app`. Leave the Build Command and Output Directory at their defaults. Do not start Uvicorn with a Vercel command; Vercel loads `main:app` as a serverless function.

### Migrations

Run Alembic from a local terminal or CI job, never on every serverless request:

```powershell
cd services/auth-service
$env:DATABASE_URL="postgresql+psycopg://..."
python -m alembic upgrade head

cd ../finance-service
python -m alembic upgrade head
```

Report Service is read-only and has no migrations of its own.

### Vercel limitations to account for

- Python services run as serverless functions, not permanent Uvicorn processes.
- Do not use local SQLite, local files, workers or long-running background jobs.
- Use Supabase for all persistent state.
- Use the Supabase pooler connection for serverless database access.
- Expect cold starts on the first request after inactivity.
- Keep report queries bounded by date range and user; add aggregates if data grows.

The frontend and backend are independent applications:

- `frontend/` is a static site served by Nginx on port 80.
- `services/auth-service/` is a FastAPI API on port 8000.
- Supabase is the external PostgreSQL and authentication data service.

## Backend

From `services/auth-service/`, provide these environment variables through the deployment platform:

```text
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://app.example.com
```

Run the migration once, then start the container:

```powershell
python -m alembic upgrade head
docker build -t personal-finance-auth .
docker run --env-file .env -p 8000:8000 personal-finance-auth
```

## Frontend

Set the three deployed API URLs in `frontend/config.js`:

```javascript
window.APP_CONFIG = {
  AUTH_API_URL: "https://auth-service.example.com/api/v1",
  FINANCE_API_URL: "https://finance-service.example.com/api/v1",
  REPORT_API_URL: "https://report-service.example.com/api/v1",
};
```

Then build and serve it independently:

```powershell
docker build -t personal-finance-frontend .
docker run -p 8080:80 personal-finance-frontend
```

The backend must list the frontend origin in `CORS_ORIGINS`. No backend source file is copied into the frontend image, and no frontend source file is copied into the backend image.