from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TariffCreate(BaseModel):
    method: str
    price_per_kg: Decimal
    price_per_m3: Decimal | None = None
    currency: str = "USD"


class TariffUpdate(BaseModel):
    price_per_kg: Decimal | None = None
    price_per_m3: Decimal | None = None
    currency: str | None = None


class TariffResponse(BaseModel):
    id: int
    method: str
    price_per_kg: Decimal
    price_per_m3: Decimal | None = None
    currency: str
    is_active: bool
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
