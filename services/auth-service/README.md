# Auth Service

Authentication service for the Personal Finance platform.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000` and its OpenAPI documentation at `/docs`.

## Probar desde el navegador

Abre `http://127.0.0.1:8000/docs`, despliega `POST /api/v1/auth/login`, pulsa **Try it out**, usa este cuerpo y pulsa **Execute**:

```json
{
	"email": "usuario@example.com",
	"password": "Strong-password1"
}
```

El login es `POST` por seguridad: las credenciales viajan en el cuerpo JSON y no en la URL. La respuesta correcta contiene `access_token`, que puedes usar en **Authorize** para probar `GET /api/v1/auth/me`.

## Endpoints

- `GET /health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me` (requiere `Authorization: Bearer <token>`)

Users are persisted through SQLAlchemy and PostgreSQL. Set a strong `SECRET_KEY` in the environment before deployment.

Supabase is configured with `SUPABASE_URL` and `SUPABASE_KEY` in `.env`. Use `get_supabase_client()` from `app.core.supabase` when a route or repository needs to access Supabase.

## Database migrations

Set `DATABASE_URL` to the PostgreSQL connection string from Supabase Dashboard > Connect, then run:

```powershell
alembic upgrade head
```

Start the API from the same terminal where `DATABASE_URL` is configured. Do not use the placeholder `localhost` URL in `.env`:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres.USER:YOUR_PASSWORD@HOST:5432/postgres"
python -m uvicorn app.main:app --reload
```

The API now fails with a connection error after 10 seconds instead of leaving requests pending indefinitely.

The first migration creates the `users` table. Do not commit the database password or `.env`.

The migration also enables RLS on `public.users` and `public.alembic_version`, and revokes direct access for the Supabase `anon` and `authenticated` roles. The FastAPI backend continues to access these tables through its PostgreSQL connection.

## Tests

```powershell
pytest
```
