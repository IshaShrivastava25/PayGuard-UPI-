"""Settings, read from environment variables (or backend/.env). Never hard-code secrets."""
import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("payguard")

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

# PostgreSQL in normal use, e.g. postgresql+psycopg://user:password@localhost:5432/payguard
# If unset, fall back to a local SQLite file so the app (and the tests) still run.
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{(BACKEND_DIR / 'payguard.db').as_posix()}"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ALLOW_REGISTRATION = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"

SECRET_KEY = os.getenv("PAYGUARD_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning(
        "PAYGUARD_SECRET_KEY is not set: using a random key, so logins are invalidated on every "
        "restart. Set it in backend/.env."
    )
