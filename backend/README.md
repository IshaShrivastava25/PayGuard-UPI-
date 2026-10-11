# PayGuard backend

FastAPI scoring service with JWT login and a stored prediction history (PostgreSQL).

## One-time setup

1. Create the database (psql, as the postgres superuser):

       CREATE USER payguard WITH PASSWORD 'choose-a-password';
       CREATE DATABASE payguard OWNER payguard;

2. Copy `.env.example` to `.env` and fill it in (`.env` is git-ignored, never commit it):

       PAYGUARD_SECRET_KEY=   <- python -c "import secrets; print(secrets.token_urlsafe(48))"
       DATABASE_URL=postgresql+psycopg://payguard:choose-a-password@localhost:5432/payguard

3. Install, inside the same venv you trained in:

       pip install -r requirements.txt

## Run

    python tests/parity_check.py          # live features == training features (must print PARITY OK)
    python -m pytest tests/test_api.py -v # auth + history tests, on a throwaway SQLite DB
    uvicorn app.main:app --reload         # docs at http://127.0.0.1:8000/docs

Tables are created automatically on first start. If DATABASE_URL is not set the app falls back
to a local SQLite file (payguard.db) so it still runs.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET  | /health | no | model name, variant, feature count |
| POST | /auth/register | no* | create an analyst (*disable with ALLOW_REGISTRATION=false) |
| POST | /auth/login | no | form fields username + password -> bearer token |
| GET  | /auth/me | yes | current user |
| POST | /predict | yes | score a transaction, store it, return explanation |
| GET  | /predictions | yes | your history (limit, offset, label filter), newest first |
| GET  | /predictions/{id} | yes | one stored prediction (404 if it isn't yours) |

In Swagger UI use the Authorize button (username + password) and then try /predict.

## Known limitations

- No login rate limiting or token revocation; tokens last ACCESS_TOKEN_EXPIRE_MINUTES.
- Tables are created with create_all; use Alembic for schema changes once data matters.
- Anyone can register unless ALLOW_REGISTRATION=false.
- Send transaction timestamps as local time without a UTC offset; the hour is used as written.
