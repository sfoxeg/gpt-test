# CatchMe backend

Layered async FastAPI backend inspired by ClimDate. HTTP routers, repositories, ORM models, Pydantic schemas, settings and dependencies are separated.

## Database migrations

Alembic owns the database schema. The application no longer creates tables at startup.

- Apply migrations: `docker compose up --build` (backend container runs `alembic upgrade head` before Uvicorn).
- Apply manually: `cd backend && alembic upgrade head`.
- Current revision: `0001_initial`.
- Inspect current revision: `alembic current`.
- Generate a revision after model changes: `alembic revision --autogenerate -m "describe change"`.
- Roll back one revision: `alembic downgrade -1`.

For an existing database previously created with `create_all`, take a backup first. If it already has the exact schema represented by revision `0001_initial`, mark it as managed with `alembic stamp 0001_initial` rather than applying the initial migration on top of existing tables. Verify the schema before stamping.

## Tests

Tests use an isolated in-memory SQLite database and do not touch the development PostgreSQL volume.

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

The suite covers repository persistence/search/chat flows and HTTP API registration, login, authenticated profile access/update and authorization.

## Runtime

Run from repository root with `docker compose up --build`. API docs: http://localhost:8000/docs.
