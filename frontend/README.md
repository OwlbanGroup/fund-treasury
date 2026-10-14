# Fund Treasury — Frontend

React + Vite + TypeScript UI for the Fund Treasury API in
[`../backend`](../backend/README.md).

## Features

- **Dashboard** — balance totals, pending/sent payment counts, latest forecast
  closing balance, recent payments.
- **Entities** — list / create / delete legal entities.
- **Accounts** — list (filterable by entity) / create / delete bank accounts.
- **Payments** — create a pending payment, then dispatch it with one click;
  shows the bank reference and outbox file returned by the bank client.
  Backend errors (e.g. duplicate reference → 409) surface inline.
- **Forecast** — pull a 14-day forecast from (mock) Kyriba, with summary cards,
  a dependency-free SVG chart (closing balance line + inflow/outflow bars) and
  a daily detail table.

All money arrives from the API as decimal strings (Pydantic serialises
`Decimal` that way) and is parsed only for display/aggregation — see
`src/api.ts`.

## Quick start

```powershell
cd frontend
npm install

# Terminal 1 — backend (mock modes are the default)
cd ../backend
.\run.ps1

# Terminal 2 — frontend dev server (proxies API calls to 127.0.0.1:8000)
npm run dev
```

Open <http://localhost:5173>. The dev server proxies `/health`, `/entities`,
`/accounts`, `/payments`, `/docs` and `/openapi.json` to the backend, so no
CORS configuration is needed in development.

### Scripts

| Command | Purpose |
| ------- | ------- |
| `npm run dev` | Start the dev server on port 5173 |
| `npm run build` | Typecheck (`tsc --noEmit`) + production build to `dist/` |
| `npm run typecheck` | Typecheck only |
| `npm run preview` | Serve the production build |

To point the built app at a non-local API, set `VITE_API_URL` (base URL,
default empty = same origin) at build time.

## Project layout

```
frontend/
├── index.html
├── vite.config.ts     # dev proxy → 127.0.0.1:8000 (override: VITE_API_PROXY)
├── src/
│   ├── main.tsx       # entry: BrowserRouter + styles
│   ├── App.tsx        # sidebar layout, routes, health badge
│   ├── api.ts         # typed API client mirroring backend schemas
│   ├── styles.css     # all styling (no CSS framework)
│   └── pages/         # Dashboard, Entities, Accounts, Payments, Forecast
```
