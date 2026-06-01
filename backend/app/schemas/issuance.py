from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class IssuanceCreate(BaseModel):
    client_id: int
    parcel_ids: list[int]
    payment_method: str | None = None
    payment_status: str


class IssuanceItemResponse(BaseModel):
    id: int
    parcel_id: int
    weight_kg: Decimal
    volume_m3: Decimal | None = None
    delivery_method: str
    tariff_applied: Decimal
    amount: Decimal

    model_config = {"from_attributes": True}


class IssuanceResponse(BaseModel):
    id: int
    client_id: int
    staff_id: int
    total_weight: Decimal
    total_amount: Decimal
    payment_status: str
    payment_method: str | None = None
    issued_at: datetime
    items: list[IssuanceItemResponse] = []

    model_config = {"from_attributes": True}
