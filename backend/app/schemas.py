from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- auth ----------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:  # bcrypt only uses the first 72 bytes
            raise ValueError("Password must be at most 72 bytes")
        return v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- scoring ----------
class TransactionIn(BaseModel):
    sender_vpa: str = Field(min_length=3, max_length=100)
    receiver_vpa: str = Field(min_length=3, max_length=100)
    # Local time of the transaction. Send it without a UTC offset: the hour is used as written.
    timestamp: datetime
    transaction_mode: Literal["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
    amount: float = Field(gt=0)
    sender_balance_before: float = Field(ge=0)
    sender_balance_after: float = Field(ge=0)
    receiver_balance_before: float = Field(ge=0)
    receiver_balance_after: float = Field(ge=0)


class Contributor(BaseModel):
    feature: str
    label: str
    value: float          # raw (unscaled) value the analyst can recognise
    contribution: float   # SHAP value in log-odds; sign shows direction
    direction: Literal["toward_fraud", "toward_normal"]


class PredictionOut(BaseModel):
    prediction_id: int
    risk_score: float
    label: Literal["fraud", "not_fraud"]
    threshold: float
    model_name: str
    preprocessing_variant: str
    top_contributors: List[Contributor]


# ---------- history ----------
class PredictionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    sender_vpa: str
    receiver_vpa: str
    tx_timestamp: datetime
    transaction_mode: str
    amount: float
    risk_score: float
    label: Literal["fraud", "not_fraud"]
    threshold: float
    model_name: str
    model_variant: str
    top_contributors: List[Contributor]

    @field_validator("created_at")
    @classmethod
    def assume_utc(cls, v: datetime) -> datetime:
        # SQLite hands back naive datetimes; PostgreSQL hands back aware ones. Always emit UTC.
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v
