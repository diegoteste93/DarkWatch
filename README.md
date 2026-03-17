# DarkWatch (MVP SaaS - Hardened API)

Backend multi-tenant para monitoramento de vazamentos com LeakRadar.

## Stack
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- APScheduler
- Docker Compose

## Subir ambiente
```bash
cp .env.example .env
docker compose up -d --build
```

API: `http://localhost:9003`  
Postgres host: `localhost:5433`

## Bootstrap admin
```bash
docker compose run --rm api python -m app.bootstrap --email admin@darkwatch.local --password Admin123!
```

## Contratos HTTP

### Sucesso padrão
```json
{
  "data": {},
  "message": "Success"
}
```

### Paginação padrão
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 50,
  "pages": 2
}
```

### Erro padrão
```json
{
  "detail": "Mensagem clara",
  "code": "ERROR_CODE",
  "status": 409
}
```

## Roles (RBAC)
- `ADMIN`: acesso global.
- `CLIENT`: acesso apenas ao próprio tenant.

## Endpoints principais

### Auth
- `POST /auth/login`
- `GET /auth/me`

### Tenants
- `GET /tenants`
- `POST /tenants`
- `GET /tenants/{id}`
- `PATCH /tenants/{id}`

### Targets
- `GET /tenants/{id}/targets`
- `POST /tenants/{id}/targets`
- `PATCH /tenants/{id}/targets/{target_id}`

### Findings
- `GET /tenants/{id}/findings` (paginação + filtros)

### Runs / Scan
- `GET /tenants/{id}/runs`
- `GET /tenants/{id}/runs/{run_id}`
- `POST /tenants/{id}/scan`

### Settings / SMTP
- `GET /tenants/{id}/settings`
- `PATCH /tenants/{id}/settings`
- `POST /tenants/{id}/settings/test-email`

### Dashboard
- `GET /admin/dashboard/overview`
- `GET /tenants/{id}/dashboard/overview`

## Status de scan
- `pending`
- `running`
- `completed`
- `partial_failed`
- `failed`

## Testes
```bash
pytest -q
```

## Frontend (Next.js SaaS UI)

O frontend completo foi adicionado em `frontend/` com:
- Next.js App Router + TypeScript
- TailwindCSS (dark mode padrão)
- componentes estilo shadcn/ui
- TanStack Query
- Axios com interceptors JWT
- Zustand (auth state)
- Recharts

### Rotas
- `/login`
- `/admin` (console ADMIN)
- `/dashboard` (portal CLIENT)

### Executar frontend
```bash
cd frontend
npm install
npm run dev
```

Ou via compose (API + frontend):
```bash
docker compose up -d --build
```

Frontend: `http://localhost:9004`
API: `http://localhost:9003`
