from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..db_models import Prediction, User
from ..deps import get_current_user
from ..schemas import PredictionOut, PredictionRecord, TransactionIn

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictionOut)
def predict(
    tx: TransactionIn,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = request.app.state.model_service
    payload = tx.model_dump()
    payload["receiver_is_merchant"] = int(tx.receiver_vpa.lower().startswith("merchant"))
    result = svc.predict(payload)

    record = Prediction(
        user_id=user.id,
        sender_vpa=tx.sender_vpa,
        receiver_vpa=tx.receiver_vpa,
        tx_timestamp=tx.timestamp.replace(tzinfo=None),  # keep the hour as entered
        transaction_mode=tx.transaction_mode,
        amount=tx.amount,
        sender_balance_before=tx.sender_balance_before,
        sender_balance_after=tx.sender_balance_after,
        receiver_balance_before=tx.receiver_balance_before,
        receiver_balance_after=tx.receiver_balance_after,
        risk_score=result["risk_score"],
        label=result["label"],
        threshold=result["threshold"],
        model_name=result["model_name"],
        model_variant=result["preprocessing_variant"],
        top_contributors=result["top_contributors"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {**result, "prediction_id": record.id}


@router.get("/predictions", response_model=List[PredictionRecord])
def list_predictions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    label: Optional[Literal["fraud", "not_fraud"]] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Prediction).where(Prediction.user_id == user.id)
    if label:
        stmt = stmt.where(Prediction.label == label)
    stmt = stmt.order_by(Prediction.id.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/predictions/{prediction_id}", response_model=PredictionRecord)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.get(Prediction, prediction_id)
    if record is None or record.user_id != user.id:  # 404 either way: don't reveal other users' ids
        raise HTTPException(status_code=404, detail="Prediction not found")
    return record
