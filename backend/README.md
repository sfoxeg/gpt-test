# Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `DATABASE_URL` and `SECRET_KEY` in the environment. Interactive API docs: http://localhost:8000/docs.

The API includes email/password registration and login, JWT auth, editable user/climbing profiles, paginated partner search and member-only chat/message endpoints. Database tables are created automatically for this initial scaffold; use Alembic migrations before production.
