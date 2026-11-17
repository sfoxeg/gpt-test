# Backend

The API uses FastAPI with SQLAlchemy 2 async sessions and the asyncpg PostgreSQL driver.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `DATABASE_URL` and `SECRET_KEY` in the environment. For PostgreSQL, use the async URL format:

```text
postgresql+asyncpg://user:password@localhost:5432/database
```

Interactive API docs: http://localhost:8000/docs.

Database access is performed with `AsyncSession`, `await db.execute()`, `await db.commit()` and related async SQLAlchemy methods. Tables are created at application startup for this initial scaffold; use Alembic migrations before production.
