from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import db_models  # noqa: F401  (registers tables with SQLAlchemy before create_all)
from .database import Base, engine
from .model_service import ModelService
from .routers import auth, predictions


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)         # creates tables on first run (Alembic later)
    app.state.model_service = ModelService()      # load model + SHAP explainer once
    yield


app = FastAPI(title="PayGuard API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predictions.router)


@app.get("/health")
def health(request: Request):
    svc = request.app.state.model_service
    return {
        "status": "ok",
        "model": svc.model_name,
        "variant": svc.variant,
        "n_features": len(svc.feature_cols),
    }
