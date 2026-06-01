from datetime import datetime

from pydantic import BaseModel


class WarehouseCreate(BaseModel):
    name: str
    type: str
    country: str | None = None
    city: str | None = None
    phone: str
    region: str
    address: str


class WarehouseUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    country: str | None = None
    city: str | None = None
    phone: str | None = None
    region: str | None = None
    address: str | None = None
    is_active: bool | None = None


class WarehouseResponse(BaseModel):
    id: int
    name: str
    type: str
    country: str | None = None
    city: str | None = None
    phone: str
    region: str
    address: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
