# Ledger Frontend

Frontend estático de la plataforma Personal Finance. Se despliega separado de Auth, Finance y Report Service.

## Desarrollo local

```powershell
cd frontend
python -m http.server 5500
```

Abre `http://127.0.0.1:5500`.

El frontend espera estos servicios:

```javascript
window.APP_CONFIG = {
  AUTH_API_URL: "http://127.0.0.1:8000/api/v1",
  FINANCE_API_URL: "http://127.0.0.1:8001/api/v1",
  REPORT_API_URL: "http://127.0.0.1:8002/api/v1",
};
```

## Despliegue en Vercel

Crea un proyecto Vercel con:

```text
Root Directory: frontend
Framework Preset: Other
Build Command: vacío
Output Directory: .
```

Antes de desplegar, edita `config.js` con las URLs públicas de los tres microservicios:

```javascript
window.APP_CONFIG = {
  AUTH_API_URL: "https://auth-service.example.vercel.app/api/v1",
  FINANCE_API_URL: "https://finance-service.example.vercel.app/api/v1",
  REPORT_API_URL: "https://report-service.example.vercel.app/api/v1",
};
```

`config.js` contiene únicamente URLs públicas. No debe contener `DATABASE_URL`, contraseñas, `SECRET_KEY` ni claves privadas.

## Funcionalidades

- Registro y login.
- Sesión JWT en `sessionStorage`.
- Dashboard mensual en COP.
- Ingresos, gastos y balance neto.
- Flujo de caja.
- Gastos por categoría.
- Movimientos recientes.
- Cierre de sesión.

El backend debe permitir el dominio Vercel en `CORS_ORIGINS` en los tres servicios.
