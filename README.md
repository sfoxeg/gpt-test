# CatchMe — climbing partner finder

Migration of the original [Django vSite](https://github.com/sfoxeg/vSite) project to a separated API and SPA:

- **Backend:** FastAPI, SQLAlchemy 2 async API, asyncpg, PostgreSQL, JWT bearer authentication. The backend refactor inspired by ClimDate is available on `refactor/climdate-backend-patterns`.
- **Frontend:** React 19, Vite, TypeScript.
- **Infrastructure:** Docker Compose.

## Run locally

Requirements: Docker Desktop / Docker Engine with Compose.

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger / OpenAPI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

The demo frontend currently provides sign-in, partner search filters, profile viewing and profile editing. Create a user through `POST /api/auth/register` in Swagger first; then sign in from the frontend.

## Implemented API

- Registration and login by email/password; JWT-protected routes.
- User profile and climbing preferences (lead, bouldering, speed, alpinism, belay).
- Partner search with gender, goal, age, city, climbing-grade, belay and activity filters; page size up to 50 (default 8).
- Chat creation, chat list, message history and sending messages with membership checks.
- PostgreSQL persistence with asynchronous SQLAlchemy 2 `AsyncSession` sessions and the `asyncpg` driver.

## Migration notes

The original Django model fields and search behavior were used as the compatibility baseline. City is represented as a string in the new API rather than Django's integer choice ID. Existing Django database data is **not migrated automatically**; an import/mapping step is still needed if you want to carry existing accounts and uploaded avatars across. This is an initial working foundation, not a feature-for-feature port of every Django page: realtime chat, avatar uploads, password reset, email verification, production deployment hardening and Alembic migrations remain follow-up work.

Before deploying publicly, set a strong `SECRET_KEY`, configure allowed frontend origins, add database migrations and enable HTTPS.
