# CatchMe — climbing partner finder

Migration of the original [Django vSite](https://github.com/sfoxeg/vSite) project to a separated API and SPA:

- **Backend:** FastAPI, SQLAlchemy 2 async API, asyncpg, PostgreSQL, JWT bearer authentication. The backend refactor inspired by ClimDate is available on `refactor/climdate-backend-patterns`.
- **Frontend:** React 19, Vite, TypeScript, mobile-first PWA and Capacitor 7 (iOS/Android).
- **Infrastructure:** Docker Compose.

## Run locally

Requirements: Docker Desktop / Docker Engine with Compose. Copy .env.example to .env and set strong unique values for POSTGRES_PASSWORD and SECRET_KEY before starting.

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger / OpenAPI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

The frontend provides registration/login, partner search, profile editing and chat messaging. Native app setup instructions are in [frontend/README.md](frontend/README.md).

## Implemented API

- Registration and login by email/password; JWT-protected routes.
- User profile and climbing preferences (lead, bouldering, speed, alpinism, belay).
- Partner search with gender, goal, age, city, climbing-grade, belay and activity filters; page size up to 50 (default 8).
- Chat creation, chat list, message history and sending messages with membership checks.
- Authenticated WebSocket at /api/v1/ws?token=JWT for instant message delivery, typing events, presence and read receipts. REST remains available for history and sending.
- Online status is scoped to users who share a chat. Presence is process-local; use one backend worker or add Redis pub/sub before scaling horizontally.
- Messages are marked read when the recipient opens the conversation; the sender receives a messages.read event.
- PostgreSQL persistence with asynchronous SQLAlchemy 2 `AsyncSession` sessions and the `asyncpg` driver.

## Migration notes

The original Django model fields and search behavior were used as the compatibility baseline. City is represented as a string in the new API rather than Django's integer choice ID. Existing Django database data is **not migrated automatically**; an import/mapping step is still needed if you want to carry existing accounts and uploaded avatars across. This is an initial working foundation, not a feature-for-feature port of every Django page: avatar uploads, password reset and email verification remain follow-up work.

Before deploying publicly, set a strong `SECRET_KEY`, configure allowed frontend origins, add database migrations and enable HTTPS.

## Real-time chat protocol

The WebSocket accepts JSON events with type=typing or type=read and a chat_id. The server emits message, presence, typing and messages.read events. Authentication uses the same JWT as the REST API. Use WSS whenever the API is served over HTTPS.

For Android/iOS builds, set VITE_API_URL to a hostname reachable from the device (not localhost on a physical phone), use HTTPS/WSS in production, then run npm run cap:sync and open the native project with the Capacitor scripts.
