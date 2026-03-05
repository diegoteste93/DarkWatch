# DarkWatch (MVP SaaS)

MVP multi-tenant para monitoramento de vazamentos com **LeakRadar API** usando:
- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- APScheduler (scan a cada 6h dentro da API)
- Docker Compose

## 1) Subir ambiente

```bash
cp .env.example .env
# edite LEAKRADAR_API_KEY e JWT_SECRET_KEY
docker compose up --build
```

API: `http://localhost:8000`

## 2) Rodar migrations manualmente (opcional)

```bash
docker compose run --rm api alembic upgrade head
```

## 3) Criar admin

```bash
docker compose run --rm api python -m app.bootstrap --email admin@darkwatch.local --password Admin123!
```

## 4) Fluxo básico de uso

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@darkwatch.local","password":"Admin123!"}'
```

### Criar tenant (admin)
```bash
curl -X POST http://localhost:8000/tenants \
  -H "Authorization: Bearer <TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme"}'
```

### Cadastrar targets
```bash
curl -X POST http://localhost:8000/tenants/1/targets \
  -H "Authorization: Bearer <TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"type":"domain","value":"acme.com","active":true}'

curl -X POST http://localhost:8000/tenants/1/targets \
  -H "Authorization: Bearer <TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"type":"email","value":"security@acme.com","active":true}'

curl -X POST http://localhost:8000/tenants/1/targets \
  -H "Authorization: Bearer <TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"type":"keyword","value":"acme","active":true}'
```

### Rodar scan imediato
```bash
curl -X POST http://localhost:8000/tenants/1/scan \
  -H "Authorization: Bearer <TOKEN>"
```

### Listar findings
```bash
curl "http://localhost:8000/tenants/1/findings?since=2026-01-01T00:00:00" \
  -H "Authorization: Bearer <TOKEN>"
```

## Endpoints implementados
- `POST /auth/login`
- `POST /tenants` (admin)
- `POST /tenants/{tenant_id}/targets`
- `GET /tenants/{tenant_id}/findings?since=...`
- `POST /tenants/{tenant_id}/scan`
- `GET /health`

## LeakRadar client
Arquivo: `app/leakradar_client.py`
- `search_email(email, page=1, page_size=100, auto_unlock=False)` -> `POST /search/email`
- `search_domain(domain, category, page=1, page_size=100, auto_unlock=False)` -> `GET /search/domain/{domain}/{category}`
- `search_dark_web(query, page=1, page_size=25, sources=None, date_from=None, date_to=None)` -> `POST /search/dark-web`

## Observações
- Deduplicação: `unique(tenant_id, external_id)`.
- `external_id`: usa `id` do provider; fallback para hash SHA-256 de campos principais.
- Scan agendado automático a cada 6h por tenant.
