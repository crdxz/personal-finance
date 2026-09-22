# Deployment separation

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