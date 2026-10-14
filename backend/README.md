# Fund Treasury API

An end-to-end, self-contained treasury management backend. It models legal
entities, bank accounts, outbound payments and cash forecasts, and integrates
with a Kyriba-style TMS and bank connectivity — all in **offline mock mode by
default** so it runs with zero external services.

Built with **FastAPI + SQLAlchemy 2.0 + Pydantic v2** on Python 3.11.

> A React + Vite frontend lives in [`../frontend`](../frontend/README.md).


## Features

- **Entities & bank accounts** — full CRUD with validation and 409 conflict guards.
- **Payments** — create a pending payment, then dispatch it via the bank client.
  In mock mode this writes a real payment-instruction file to an `outbox/`
  directory and returns a bank reference. Double-sending and duplicate payment
  references are rejected (HTTP 409).
- **Cash forecasts** — pull a 14-day forecast from the (mock) Kyriba client and
  persist it locally; `closing_balance = opening + inflows − outflows`.
- **Configurable integrations** — `KYRIBA_MODE` / `BANK_MODE` switch between
  offline mock data and real HTTP integrations (`real` mode raises loudly if the
  transport isn't wired up, rather than silently faking success).
- **Seeded demo data** — on first start it creates one entity (`RW-CAP`) and two
  bank accounts so the API is immediately explorable.

## Quick start

```powershell
cd backend
pip install -r requirements.txt

# Run the API (mock modes are the default)
.\run.ps1
# ...or: python -m uvicorn app.main:app --reload --port 8000
```

Then open the interactive docs at <http://127.0.0.1:8000/docs>.

### Run the tests

```powershell
.\run.ps1 -Test
# ...or: python -m pytest -v
```

The suite runs against an isolated temp database/outbox (see `conftest.py`) and
covers the health endpoints, entity/account CRUD, the full payment lifecycle,
the forecast pull/read flow, the Kyriba balances endpoint, and the real-mode
client code paths (token flow + error mapping) via `httpx.MockTransport` — no
network I/O required.

## End-to-end demo (curl / PowerShell)

```powershell
$b = "http://127.0.0.1:8000"

# 1. Health
Invoke-RestMethod "$b/health"

# 2. Seeded accounts
$acc = Invoke-RestMethod "$b/accounts"
$acc[0].id   # e.g. 1

# 3. Create a pending payment
Invoke-RestMethod "$b/payments" -Method Post -ContentType "application/json" `
  -Body '{"account_id":1,"amount":"2500.75","counterparty":"Vendor Co","reference":"INV-001","payment_method":"ACH"}'

# 4. Send it -> status 'sent', writes outbox/payment_1_<id>.txt
Invoke-RestMethod "$b/payments/1/send" -Method Post

# 5. Pull + read a cash forecast
Invoke-RestMethod "$b/entities/1/forecast/pull" -Method Post
Invoke-RestMethod "$b/entities/1/forecast"

# 6. Live account balances from (mock) Kyriba
Invoke-RestMethod "$b/entities/1/balances"
```

## API surface

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Liveness + current integration modes |
| GET/POST | `/entities` | List / create entities |
| GET/PATCH/DELETE | `/entities/{id}` | Read / update / delete an entity |
| GET/POST | `/accounts` | List (optionally by `?entity_id=`) / create accounts |
| GET/PATCH/DELETE | `/accounts/{id}` | Read / update / delete an account |
| GET/POST | `/payments` | List / create a pending payment |
| GET | `/payments/{id}` | Read one payment |
| POST | `/payments/{id}/send` | Dispatch via the bank client (writes outbox file) |
| POST | `/entities/{id}/forecast/pull` | Pull a forecast from Kyriba and persist it |
| GET | `/entities/{id}/forecast` | Read the stored forecast |
| GET | `/entities/{id}/balances` | Live account balances from Kyriba (mock or real); 502 if Kyriba fails |

## Configuration

Copy `.env.example` to `.env` and edit, or set environment variables directly.

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `DATABASE_URL` | `sqlite:///./treasury.db` | SQLAlchemy DSN (switch to Postgres by changing this) |
| `KYRIBA_MODE` | `mock` | `mock` = offline synthetic data; `real` = HTTP to Kyriba |
| `KYRIBA_BASE_URL` / `KYRIBA_TOKEN_URL` | Kyriba API URLs | Real-mode endpoints |
| `KYRIBA_CLIENT_ID` / `KYRIBA_CLIENT_SECRET` | (empty) | Real-mode OAuth2 credentials |
| `BANK_MODE` | `mock` | `mock` = write payment file to outbox; `real` = transport stub |
| `BANK_FILE_OUTBOX` | `./outbox` | Where mock payment files are written |
| `CORS_ORIGINS` | `localhost:5173` | Allowed origins (default matches a Vite dev server) |

## Deployment (Fly.io)

The backend ships with a hardened `Dockerfile` (Python 3.11 slim, non-root
user) and a ready-to-use `fly.toml`:

```powershell
cd backend
flyctl apps create fund-treasury-api                          # once
flyctl volumes create fund_treasury_data --region iad --size 1 -a fund-treasury-api
flyctl deploy --yes
```

- SQLite and the bank file outbox live on the `/data` volume (`DATABASE_URL` and
  `BANK_FILE_OUTBOX` are set in `fly.toml`).
- `CORS_ORIGINS` in `fly.toml` already allows the deployed frontend
  (`https://fund-treasury-web.fly.dev`) alongside local dev servers.
- The machine auto-stops when idle (`min_machines_running = 0`), has a `/health`
  check, and runs in mock mode by default. Wire real Kyriba credentials with
  `flyctl secrets set KYRIBA_CLIENT_ID=... KYRIBA_CLIENT_SECRET=... -a fund-treasury-api`.
- Fly requires billing information on file before the first machine starts
  (even within the free allowance): <https://fly.io/dashboard/david-leeper-9/billing>

## Project layout

```
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS, lifespan (init DB + seed)
│   ├── config.py        # Settings from env
│   ├── database.py      # Engine, session factory, Base
│   ├── seed.py          # Idempotent demo seed
│   ├── models/          # ORM models (Entity, BankAccount, Payment, CashForecast)
│   ├── schemas/         # Pydantic request/response models
│   ├── clients/         # KyribaClient + BankClient (mock/real) and shared types
│   └── routers/         # Health, entities, accounts, balances, payments, forecast
├── tests/               # Pytest suite (isolated temp DB/outbox)
├── conftest.py          # Test fixtures
├── pytest.ini
├── requirements.txt
└── run.ps1              # One-command runner (server or tests)
```

## Switching to real integrations

- **Kyriba** — set `KYRIBA_MODE=real` and provide the base URL, token URL and
  OAuth2 credentials. `KyribaClient` then calls the documented REST endpoints.
- **Bank** — set `BANK_MODE=real` and implement the transport in
  `BankClient._real_send` (SFTP/H2H is environment-specific). Until then it
  raises `BankError` so no half-configured submission ever pretends to succeed.
