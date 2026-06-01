from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ParcelChinaCreate(BaseModel):
    track_id: str


class ParcelChinaBulk(BaseModel):
    track_ids: list[str]


class ParcelChinaResponse(BaseModel):
    id: int
    track_id: str
    warehouse_id: int | None = None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ParcelDushanbeCreate(BaseModel):
    track_id: str
    tps_code: str
    weight_kg: Decimal
    volume_m3: Decimal | None = None
    delivery_method: str
    comment: str | None = None


class ParcelDushanbeResponse(BaseModel):
    id: int
    track_id: str
    client_id: int
    status: str
    weight_kg: Decimal
    volume_m3: Decimal | None = None
    delivery_method: str
    warehouse_id: int | None = None
    amount_due: Decimal | None = None
    tariff_snapshot: Decimal | None = None
    has_china_registration: bool
    comment: str | None = None
    notified_at: datetime | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ParcelStatusUpdate(BaseModel):
    status: str


class ParcelUpdate(BaseModel):
    weight_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    delivery_method: str | None = None
    comment: str | None = None
    status: str | None = None
