from datetime import datetime

from pydantic import BaseModel


class ClientRegister(BaseModel):
    telegram_id: int
    full_name: str
    phone: str
    address: str | None = None
    lang: str = "ru"


class ClientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    lang: str | None = None


class ClientResponse(BaseModel):
    id: int
    telegram_id: int
    tps_code: str
    full_name: str
    phone: str
    address: str | None = None
    lang: str
    status: str
    created_at: datetime
    last_activity_at: datetime | None = None

    model_config = {"from_attributes": True}
