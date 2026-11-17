# CatchMe backend

Backend architecture is based on the layered style used in ClimDate:

- `api/v1/routers`: HTTP routing and request/response boundaries.
- `core/repositories`: async database operations and persistence queries.
- `core/models`: SQLAlchemy ORM entities, declarative base and mixins.
- `core/schemas`: Pydantic request/response contracts.
- `core/settings`: separate application and database configuration.
- `core/dependencies.py`: authentication dependencies.
- `core/database.py`: async engine and session factory.

All database access uses SQLAlchemy async sessions via `async with new_session()`; PostgreSQL uses asyncpg.

Run with Docker Compose from the repository root. API docs: http://localhost:8000/docs.

Alembic is included as the migration dependency. Before production, add and apply migrations rather than relying on the development `create_all` bootstrap.
